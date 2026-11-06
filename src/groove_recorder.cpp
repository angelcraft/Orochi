#include "groove_recorder_buffer.h"
#include "hk/hook/Trampoline.h"
#include "hk/svc/cpu.h"
#include <cstdio>

namespace {
constexpr ptr kStage = 0x488940, kWait = 0x514d70, kHoop = 0x217960, kLoop = 0x509e10;
constexpr u8 kBuild[] = {0x03,0xff,0x4a,0x3b,0xec,0x96,0xbd,0xe3,
                         0xa2,0xe3,0x7c,0xe3,0xaa,0x4c,0xaa,0x0c};
constexpr u32 kUnknownStage = 0xffffffff;
enum Kind { StageCreated = 1, WaitRequested, HoopCalled };

groove::Buffer<1024> buffer;
std::atomic<u32> lastCreatedStage{kUnknownStage};
std::atomic_flag draining = ATOMIC_FLAG_INIT;
u64 session{}, reportedLoss{};

void emit(const char* text, int size) {
    if (size > 0) (void)hk::svc::OutputDebugString(text, size);
}

u32 threadTick(const void* thread) {
    return thread ? *reinterpret_cast<const u32*>(static_cast<const char*>(thread) + 0x278) : 0xffffffff;
}

void record(Kind kind, s32 value, const void* thread) {
    buffer.push({0, hk::svc::getSystemTick(), kind, lastCreatedStage.load(std::memory_order_relaxed), value, threadTick(thread)});
}

HkTrampoline stageHook = [](TrampolineStatic(), u32 id, u64 a2, u32 a3, u32 a4, u32 a5, u32 a6, u32 a7) -> void* {
    auto* result = orig(id, a2, a3, a4, a5, a6, a7);
    if (result) {
        lastCreatedStage.store(id, std::memory_order_relaxed);
        buffer.push({0, hk::svc::getSystemTick(), StageCreated, id, 0, 0xffffffff});
    }
    return result;
};

HkTrampoline waitHook = [](TrampolineStatic(), void* thread, s32 ticks) -> void {
    record(WaitRequested, ticks, thread);
    orig(thread, ticks);
};

HkTrampoline hoopHook = [](TrampolineStatic(), void* scene, void* thread, s32 bubbleState) -> void {
    record(HoopCalled, bubbleState, thread);
    orig(scene, thread, bubbleState);
};

void drain() {
    if (draining.test_and_set(std::memory_order_acquire)) return;
    char packet[3072];
    int used = 0;
    for (int index = 0; index < 16; ++index) {
        groove::Event event;
        if (!buffer.pop(event)) break;
        const int size = std::snprintf(packet + used, sizeof(packet) - used,
            "GROOVE_REC %llu %llu %llu %u %u %d %u\n",
            (unsigned long long)session, (unsigned long long)event.sequence,
            (unsigned long long)event.counter, event.kind, event.stage, event.value, event.threadTick);
        if (size < 0 || size >= static_cast<int>(sizeof(packet) - used)) break;
        used += size;
    }
    emit(packet, used);
    const u64 loss = buffer.dropped();
    if (loss != reportedLoss) {
        const int size = std::snprintf(packet, sizeof(packet), "GROOVE_LOST %llu %llu\n",
            (unsigned long long)session, (unsigned long long)loss);
        if (size > 0 && size < static_cast<int>(sizeof(packet))) emit(packet, size);
        reportedLoss = loss;
    }
    draining.clear(std::memory_order_release);
}

HkTrampoline loopHook = [](TrampolineStatic(), s32 argument) -> void {
    orig(argument);
    drain();
};
}

extern "C" void hkMain() {
    auto* module = hk::ro::getMainModule();
    static_assert(sizeof(kBuild) == hk::ro::cBuildIdSize);
    if (!module || !module->getBuildId() ||
        __builtin_memcmp(module->getBuildId(), kBuild, sizeof(kBuild)) != 0) return;
    const auto base = module->range().start();
    const auto expected = [base](ptr offset, u32 word) {
        return *reinterpret_cast<const u32*>(base + offset) == word;
    };
    if (!expected(kLoop, 0x900044a8) || !expected(kStage, 0xa9bb7bfd) ||
        !expected(kWait, 0xb9427808) || !expected(kHoop, 0xd102c3ff) ||
        !expected(kLoop+4, 0x900044a9) || !expected(kStage+4, 0xf9000bf9) ||
        !expected(kWait+4, 0x0b010108) || !expected(kHoop+4, 0xa9057bfd)) return;
    session = hk::svc::getSystemTick();
    if (loopHook.installAtMainOffset(kLoop).failed()) return;
    const unsigned stage = stageHook.installAtMainOffset(kStage).succeeded();
    const unsigned wait = waitHook.installAtMainOffset(kWait).succeeded();
    const unsigned hoop = hoopHook.installAtMainOffset(kHoop).succeeded();
    char header[180];
    const int size = std::snprintf(header, sizeof(header), "GROOVE_SESSION %llu %llu %u %u %u\n",
        (unsigned long long)session, (unsigned long long)hk::svc::getSystemTickFrequency(), stage, wait, hoop);
    if (size > 0 && size < static_cast<int>(sizeof(header))) emit(header, size);
}
