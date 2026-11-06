#include "groove_recorder_buffer.h"
#include "hk/hook/Trampoline.h"
#include "hk/svc/cpu.h"
#include "aloha/WavMark.h"
#include <cstdio>

namespace {
// Groove 1.0.0 (Build ID guarded below). All offsets come from Orochi's
// existing symbols; none should be reused for another game update.
constexpr ptr kStage = 0x488940;
constexpr ptr kWait = 0x514d70;
constexpr ptr kHoop = 0x217960;
constexpr ptr kLoop = 0x509e10;
constexpr ptr kScheduleSfx = 0x12bff0;
constexpr ptr kStartBgm = 0x139140;
constexpr ptr kInitSubScene = 0x4d9dc0;
constexpr ptr kEnableCues = 0x4daa70;
constexpr ptr kAppendThread = 0x5153a0;
constexpr u8 kBuild[] = {
    0x03, 0xff, 0x4a, 0x3b, 0xec, 0x96, 0xbd, 0xe3,
    0xa2, 0xe3, 0x7c, 0xe3, 0xaa, 0x4c, 0xaa, 0x0c
};
constexpr u32 kUnknown = 0xffffffff;
enum Kind : u32 {
    StageCreated = 1,
    WaitRequested = 2,
    HoopCalled = 3,
    SfxScheduled = 4,
    BgmRequested = 5,
    SubSceneInitRequested = 6,
    SubSceneCuesEnabled = 7,
    ThreadAppended = 8
};

// Every scene type can pass through the shared sequencer / audio routines.
// The recorder DOES NOT yet capture all game-specific actions, actual inputs
// or judgements; those need separately proven common hooks.
groove::Buffer<4096> buffer;
std::atomic<u32> lastCreatedStage{kUnknown};
std::atomic_flag draining = ATOMIC_FLAG_INIT;
u64 session{}, reportedLoss{};

void emit(const char* text, int size) {
    if (size > 0) (void)hk::svc::OutputDebugString(text, size);
}

// Intentionally do not dereference SeqThread+0x278: that offset has not been
// demonstrated to hold the musical beat/tick. Retain a missing-value marker
// until a native clock / thread layout can be verified on hardware.
void record(Kind kind, s32 value, s32 auxiliary = 0) {
    buffer.push({0, hk::svc::getSystemTick(), kind,
                 lastCreatedStage.load(std::memory_order_relaxed),
                 value, kUnknown, auxiliary});
}

HkTrampoline stageHook = [](TrampolineStatic(), u32 id, u64 a2, u32 a3, u32 a4, u32 a5, u32 a6, u32 a7) -> void* {
    auto* result = orig(id, a2, a3, a4, a5, a6, a7);
    if (result) {
        lastCreatedStage.store(id, std::memory_order_relaxed);
        buffer.push({0, hk::svc::getSystemTick(), StageCreated, id, 0, kUnknown, 0});
    }
    return result;
};

HkTrampoline waitHook = [](TrampolineStatic(), void* thread, s32 ticks) -> void {
    record(WaitRequested, ticks);
    orig(thread, ticks);
};

HkTrampoline hoopHook = [](TrampolineStatic(), void* scene, void* thread, s32 bubbleState) -> void {
    record(HoopCalled, bubbleState);
    orig(scene, thread, bubbleState);
};

// Common scene audio scheduling is useful for identifying cues across
// minigames, but an SFX is NOT proof of a scheduled player input.
HkTrampoline sfxHook = [](TrampolineStatic(), void* scene, void* thread,
                          s32 ticks, void* manager, u32 soundId,
                          s32 unknown, float volume, float pitch) -> void {
    record(SfxScheduled, static_cast<s32>(soundId), ticks);
    orig(scene, thread, ticks, manager, soundId, unknown, volume, pitch);
};

HkTrampoline bgmHook = [](TrampolineStatic(), void* stage, void* thread,
                          WavMarkId wavmark, u32 ticks, s32 unknown,
                          float volume, float pitch) -> void {
    record(BgmRequested, static_cast<s32>(wavmark), static_cast<s32>(ticks));
    orig(stage, thread, wavmark, ticks, unknown, volume, pitch);
};

HkTrampoline subSceneHook = [](TrampolineStatic(), void* stage,
                               s32 sceneId, s32 unknown, bool flag) -> void {
    record(SubSceneInitRequested, sceneId, unknown);
    orig(stage, sceneId, unknown, flag);
};

HkTrampoline cuesHook = [](TrampolineStatic(), void* stage,
                           void* thread, s32 sceneId) -> void {
    record(SubSceneCuesEnabled, sceneId);
    orig(stage, thread, sceneId);
};

HkTrampoline appendThreadHook = [](TrampolineStatic(), void* runner,
                                   void* thread) -> void {
    orig(runner, thread);
    record(ThreadAppended, 0);
};

// Keep formatting outside the timing-sensitive hooks. Emitting at most
// 16 events / frame bounds the work; the buffer reports any dropped records.
void drain() {
    if (draining.test_and_set(std::memory_order_acquire)) return;
    char packet[3072];
    int used = 0;
    for (int index = 0; index < 16; ++index) {
        groove::Event event;
        if (!buffer.pop(event)) break;
        const int size = std::snprintf(packet + used, sizeof(packet) - used,
            "GROOVE_REC2 %llu %llu %llu %u %u %d %u %d\n",
            (unsigned long long)session,
            (unsigned long long)event.sequence,
            (unsigned long long)event.counter,
            event.kind, event.stage, event.value,
            event.threadTick, event.auxiliary);
        if (size < 0 || size >= static_cast<int>(sizeof(packet) - used)) break;
        used += size;
    }
    emit(packet, used);
    const u64 loss = buffer.dropped();
    if (loss != reportedLoss) {
        const int size = std::snprintf(packet, sizeof(packet),
            "GROOVE_LOST %llu %llu\n",
            (unsigned long long)session, (unsigned long long)loss);
        if (size > 0 && size < static_cast<int>(sizeof(packet)))
            emit(packet, size);
        reportedLoss = loss;
    }
    draining.clear(std::memory_order_release);
}

HkTrampoline loopHook = [](TrampolineStatic(), s32 argument) -> void {
    orig(argument);
    drain();
};

void diagnostic(const char* message) {
    const int size = std::snprintf(nullptr, 0, "%s", message);
    if (size > 0 && size < 140) emit(message, size);
}

} // namespace

extern "C" void hkMain() {
    diagnostic("GROOVE_DIAG recorder_v2_entered\n");
    auto* module = hk::ro::getMainModule();
    static_assert(sizeof(kBuild) == hk::ro::cBuildIdSize);
    if (!module || !module->getBuildId() ||
        __builtin_memcmp(module->getBuildId(), kBuild, sizeof(kBuild)) != 0) {
        diagnostic("GROOVE_DIAG build_id_unavailable_or_unsupported\n");
        return;
    }
    const auto base = module->range().start();
    const auto expected = [base](ptr offset, u32 word) {
        return *reinterpret_cast<const u32*>(base + offset) == word;
    };
    // Previously verified prologues. Additional hooks are bound to the
    // same Build ID, and remain UNVERIFIED in a running Switch process.
    if (!expected(kLoop, 0x900044a8) || !expected(kStage, 0xa9bb7bfd) ||
        !expected(kWait, 0xb9427808) || !expected(kHoop, 0xd102c3ff) ||
        !expected(kLoop+4, 0x900044a9) || !expected(kStage+4, 0xf9000bf9) ||
        !expected(kWait+4, 0x0b010108) || !expected(kHoop+4, 0xa9057bfd)) {
        diagnostic("GROOVE_DIAG original_hook_bytes_changed\n");
        return;
    }

    session = hk::svc::getSystemTick();
    if (loopHook.installAtMainOffset(kLoop).failed()) {
        diagnostic("GROOVE_DIAG main_loop_hook_failed\n");
        return;
    }
    const unsigned stage = stageHook.installAtMainOffset(kStage).succeeded();
    const unsigned wait = waitHook.installAtMainOffset(kWait).succeeded();
    const unsigned hoop = hoopHook.installAtMainOffset(kHoop).succeeded();
    const unsigned sfx = sfxHook.installAtMainOffset(kScheduleSfx).succeeded();
    const unsigned bgm = bgmHook.installAtMainOffset(kStartBgm).succeeded();
    const unsigned subscene = subSceneHook.installAtMainOffset(kInitSubScene).succeeded();
    const unsigned cues = cuesHook.installAtMainOffset(kEnableCues).succeeded();
    const unsigned threads = appendThreadHook.installAtMainOffset(kAppendThread).succeeded();
    char header[256];
    const int size = std::snprintf(header, sizeof(header),
        "GROOVE_SESSION2 %llu %llu %u %u %u %u %u %u %u %u\n",
        (unsigned long long)session,
        (unsigned long long)hk::svc::getSystemTickFrequency(),
        stage, wait, hoop, sfx, bgm, subscene, cues, threads);
    if (size > 0 && size < static_cast<int>(sizeof(header))) emit(header, size);
}
