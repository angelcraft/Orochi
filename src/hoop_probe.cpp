#include "hk/hook/InstrUtil.h"

namespace {
constexpr ptr kStopSite = 0x42cc80;
constexpr ptr kStop = 0x514dd0;
constexpr ptr kHoop = 0x217960;
constexpr unsigned kRingSceneOffset = 0x2ca0;
constexpr unsigned char kBuildId[] = {
    0x03, 0xff, 0x4a, 0x3b, 0xec, 0x96, 0xbd, 0xe3,
    0xa2, 0xe3, 0x7c, 0xe3, 0xaa, 0x4c, 0xaa, 0x0c,
};
ptr mainBase;
}

extern "C" unsigned hoopProbeStop(void* thread, char* stage) {
    auto stop = reinterpret_cast<unsigned (*)(void*)>(mainBase + kStop);
    const unsigned result = stop(thread);
    if ((result & 1u) == 0) {
        auto hoop = reinterpret_cast<void (*)(void*, void*, int)>(mainBase + kHoop);
        hoop(stage + kRingSceneOffset, thread, -1);
    }
    return result;
}

// This replaces a BL in the original stage routine. x20 is its live stage
// pointer, x0 is the native thread, and the original LR goes to hoopProbeStop.
extern "C" __attribute__((naked)) unsigned hoopProbeBridge(void*) {
    asm volatile("mov x1, x20\n"
                 "b hoopProbeStop\n");
}

extern "C" void hkMain() {
    auto* module = hk::ro::getMainModule();
    if (!module || !module->getBuildId()) return;
    static_assert(sizeof(kBuildId) == hk::ro::cBuildIdSize);
    if (__builtin_memcmp(module->getBuildId(), kBuildId, sizeof(kBuildId)) != 0) return;
    mainBase = module->range().start();
    const auto* site = reinterpret_cast<const unsigned*>(mainBase + kStopSite);
    if (site[-1] != 0xaa1303e0 || site[0] != 0x9403a054 || site[1] != 0x370095c0) return;
    const auto from = mainBase + kStopSite;
    const auto to = reinterpret_cast<ptr>(&hoopProbeBridge);
    const auto distance = to >= from ? to - from : from - to;
    if ((distance & 3) || distance > hk::hook::cMaxBranchDistance) return;
    (void)hk::hook::writeBranchLinkAtMainOffset(kStopSite, &hoopProbeBridge);
}

