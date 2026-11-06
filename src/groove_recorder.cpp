#include "groove_recorder_buffer.h"
#include "hk/hook/Trampoline.h"
#include "hk/svc/cpu.h"
#include "aloha/WavMark.h"
#include "aloha/Scene.h"
#include <bit>
#include <type_traits>
#include "nn/fs.h"
#include <cstdio>

namespace {
// Groove 1.0.0 (Build ID guarded below). All offsets come from Orochi's
// existing symbols; none should be reused for another game update.
constexpr ptr kStage = 0x488940;
constexpr ptr kWait = 0x514d70;
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
    ThreadAppended = 8,
    GameplayCalled = 9
};

groove::Buffer<4096> buffer;
std::atomic<u32> lastCreatedStage{kUnknown};
std::atomic_flag draining = ATOMIC_FLAG_INIT;
u64 session{}, reportedLoss{};

unsigned drainFrameCounter{};
bool sdReady = false;
bool sdMounted = false;
char storedSessionHeader[256]{};
int storedSessionHeaderLength{};
bool sdWriteFailed{};
std::atomic<u64> loopEntered{0};
u64 dequeued{}, sdBatches{}, sdFailures{};

void reportPipeline(const char* phase);
constexpr const char* kSdMount = "grooverec";
constexpr const char* kSdFolder = "grooverec:/Orochi";
constexpr const char* kSdLog = "grooverec:/Orochi/groove-recorder.log";

void diagnostic(const char* message);

// Only called during the main-loop drain path. Never do SD I/O in a gameplay hook.
bool appendFile(const char* data, int size) {
    if (!sdReady || size <= 0) return false;
    nn::fs::FileHandle file{};
    // Horizon FS requires explicit file growth before writing beyond EOF.
    // Match Orochi's original known writer instead of relying on append mode.
    if (nn::fs::OpenFile(&file, kSdLog, nn::fs::OpenMode_Write).IsFailure())
        return false;
    s64 fileSize = 0;
    bool written = false;
    if (nn::fs::GetFileSize(&fileSize, file).IsSuccess() &&
        fileSize >= 0 && fileSize <= 0x7fffffffffffffffLL - size &&
        nn::fs::SetFileSize(file, fileSize + size).IsSuccess()) {
        const auto flush = nn::fs::WriteOption::CreateOption(nn::fs::WriteOptionFlag_Flush);
        written = nn::fs::WriteFile(file, fileSize, data, size, flush).IsSuccess();
    }
    nn::fs::CloseFile(file);
    return written;
}

void initSdLogging() {
    if (!sdMounted && nn::fs::MountSdCard(kSdMount).IsFailure()) {
        diagnostic("GROOVE_DIAG sd_mount_failed\n");
        return;
    }
    sdMounted = true;
    (void)nn::fs::CreateDirectory(kSdFolder);
    (void)nn::fs::CreateFile(kSdLog, 0);
    nn::fs::FileHandle file{};
    if (nn::fs::OpenFile(&file, kSdLog, nn::fs::OpenMode_Write).IsSuccess()) {
        nn::fs::CloseFile(file);
        sdReady = true;
        diagnostic("GROOVE_DIAG sd_log_opened\n");
        // Persist a header immediately: a zero-length log after play means
        // we could not write anything, regardless of gameplay-hook coverage.
        if (storedSessionHeaderLength > 0 &&
            appendFile(storedSessionHeader, storedSessionHeaderLength)) {
            storedSessionHeaderLength = 0;
            diagnostic("GROOVE_DIAG session_header_written\n");
        } else {
            diagnostic("GROOVE_DIAG session_header_write_failed\n");
        }
        if (!draining.test_and_set(std::memory_order_acquire)) {
            reportPipeline("sd_open");
            draining.clear(std::memory_order_release);
        }
    } else {
        diagnostic("GROOVE_DIAG sd_log_open_failed\n");
    }
}


void emit(const char* text, int size) {
    if (size > 0) (void)hk::svc::OutputDebugString(text, size);
}

void reportPipeline(const char* phase) {
    char line[256];
    const int size = std::snprintf(line, sizeof(line),
        "GROOVE_DIAG pipeline phase=%s session=%llu loop=%llu queued=%llu dropped=%llu dequeued=%llu sd_batches=%llu sd_failures=%llu\n",
        phase, (unsigned long long)session, (unsigned long long)loopEntered.load(std::memory_order_relaxed),
        (unsigned long long)buffer.accepted(), (unsigned long long)buffer.dropped(),
        (unsigned long long)dequeued, (unsigned long long)sdBatches, (unsigned long long)sdFailures);
    if (size > 0 && size < static_cast<int>(sizeof(line))) {
        emit(line, size);
        appendFile(line, size);
    }
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

// Permit only a single displaced instruction. Far branches would overwrite
// additional instructions and use IP0 in the continuation.
template <typename L>
bool installChecked(const hk::ro::RoModule* module, hk::hook::Trampoline<L>& hook,
                    ptr offset, u32 expected) {
    const auto text = module->text();
    if (offset % sizeof(u32) || text.size() < sizeof(u32) ||
        offset > text.size() - sizeof(u32))
        return false;
    const ptr site = text.start() + offset;
    const auto near = [](ptr a, ptr b) {
        // Leave room for the ADRP relocation used by the loop trampoline.
        constexpr ptr limit = (ptr{1} << 27) - 32;
        return a >= b ? a - b <= limit : b - a <= limit;
    };
    const ptr replacement = reinterpret_cast<ptr>(hk::hook::detail::TrampolineFunc<L>::invoke);
    const ptr backup = reinterpret_cast<ptr>(&hk::hook::detail::TrampolineStaticBackup<L>::orig);
    return near(site, replacement) && near(backup, site) &&
           *reinterpret_cast<const u32*>(site) == expected &&
           hook.installAtOffset(module, offset).succeeded();
}

template <typename T>
s64 encodeArgument(T argument) {
    if constexpr (std::is_pointer_v<T>)
        return argument != nullptr;
    else if constexpr (std::is_same_v<T, float>)
        return std::bit_cast<u32>(argument);
    else
        return static_cast<s64>(argument);
}

template <typename... Args>
void recordGameplay(s32 command, s32 scene, Args... args) {
    static_assert(sizeof...(args) <= 4);
    buffer.push({0, hk::svc::getSystemTick(), GameplayCalled,
                 lastCreatedStage.load(std::memory_order_relaxed),
                 command, kUnknown, scene, {encodeArgument(args)...}});
}

#include "groove_gameplay_hooks.inc"

// Keep formatting outside the timing-sensitive hooks. Emitting at most
// 48 events every twelve loop calls bounds the work; the buffer counts losses.
void drain() {
    if (draining.test_and_set(std::memory_order_acquire)) return;
    if ((++drainFrameCounter % 12) != 0) {
        draining.clear(std::memory_order_release);
        return;
    }
    char packet[48 * 192];
    int used = 0;
    for (int index = 0; index < 48; ++index) {
        groove::Event event;
        if (!buffer.pop(event)) break;
        ++dequeued;
        const int size = event.kind == GameplayCalled
            ? std::snprintf(packet + used, sizeof(packet) - used,
                "GROOVE_ACTION %llu %llu %llu %u %d %d %lld %lld %lld %lld\n",
                (unsigned long long)session, (unsigned long long)event.sequence,
                (unsigned long long)event.counter, event.stage, event.value, event.auxiliary,
                (long long)event.arguments[0], (long long)event.arguments[1],
                (long long)event.arguments[2], (long long)event.arguments[3])
            : std::snprintf(packet + used, sizeof(packet) - used,
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
    if (sdReady && (storedSessionHeaderLength > 0 || used > 0)) {
        if (storedSessionHeaderLength > 0 &&
            appendFile(storedSessionHeader, storedSessionHeaderLength)) {
            storedSessionHeaderLength = 0;
        }
        const bool failed = storedSessionHeaderLength > 0 ||
                            (used > 0 && !appendFile(packet, used));
        if (failed) ++sdFailures;
        else if (used > 0) ++sdBatches;
        if (failed && !sdWriteFailed) diagnostic("GROOVE_DIAG sd_write_failed\n");
        if (!failed && sdWriteFailed) diagnostic("GROOVE_DIAG sd_write_recovered\n");
        sdWriteFailed = failed;
    }
    const u64 loss = buffer.dropped();
    if (loss != reportedLoss) {
        const int size = std::snprintf(packet, sizeof(packet),
            "GROOVE_LOST %llu %llu\n",
            (unsigned long long)session, (unsigned long long)loss);
        if (size > 0 && size < static_cast<int>(sizeof(packet))) {
            emit(packet, size);
            if (storedSessionHeaderLength == 0) appendFile(packet, size);
        }
        reportedLoss = loss;
    }
    if (drainFrameCounter == 12 || drainFrameCounter % 120 == 0)
        reportPipeline("drain");
    draining.clear(std::memory_order_release);
}

HkTrampoline initHook = [](TrampolineStatic(), u64* argument) -> void {
    if (!sdReady) initSdLogging();
    orig(argument);
};

HkTrampoline loopHook = [](TrampolineStatic(), s32 argument) -> void {
    if (loopEntered.fetch_add(1, std::memory_order_relaxed) == 0)
        diagnostic("GROOVE_DIAG loop_entered\n");
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
    session = hk::svc::getSystemTick();
    if (!installChecked(module, loopHook, kLoop, 0x900044a8)) {
        diagnostic("GROOVE_DIAG main_loop_hook_rejected\n");
        return;
    }
    const unsigned stage = installChecked(module, stageHook, kStage, 0xa9bb7bfd);
    const unsigned wait = installChecked(module, waitHook, kWait, 0xb9427808);
    const unsigned sfx = installChecked(module, sfxHook, kScheduleSfx, 0xfc190fec);
    const unsigned bgm = installChecked(module, bgmHook, kStartBgm, 0x6dba23e9);
    const unsigned subscene = installChecked(module, subSceneHook, kInitSubScene, 0x52800708);
    const unsigned cues = installChecked(module, cuesHook, kEnableCues, 0xa9bd7bfd);
    const unsigned threads = installChecked(module, appendThreadHook, kAppendThread, 0xf8408c08);
    unsigned hoop = 0;
    const unsigned gameplay = installGameplayHooks(module, hoop);
    char header[256];
    const int size = std::snprintf(header, sizeof(header),
        "GROOVE_SESSION3 %llu %llu %u %u %u %u %u %u %u %u %u\n",
        (unsigned long long)session,
        (unsigned long long)hk::svc::getSystemTickFrequency(),
        stage, wait, hoop, sfx, bgm, subscene, cues, threads, gameplay);
    if (size > 0 && size < static_cast<int>(sizeof(header))) {
        emit(header, size);
        __builtin_memcpy(storedSessionHeader, header, size);
        storedSessionHeaderLength = size;
    }
    if (!installChecked(module, initHook, 0x50cba0, 0xa9bd7bfd))
        diagnostic("GROOVE_DIAG sd_mount_hook_failed\n");
}
