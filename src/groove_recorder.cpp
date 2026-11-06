#include "groove_recorder_buffer.h"
#include "hk/hook/Trampoline.h"
#include "hk/svc/cpu.h"
#include "aloha/WavMark.h"
#include "aloha/Scene.h"
#include <bit>
#include <type_traits>
#include "nn/fs.h"
#include <cstdio>

// Imports match the ThreadType overload used by the original main NSO.
namespace nn::os {
struct ThreadType;
nn::Result CreateThread(ThreadType*, void (*)(void*), void*, void*, unsigned long, int, int);
void StartThread(ThreadType*);
}

namespace {
// Groove 1.0.0 (Build ID guarded below). All offsets come from Orochi's
// existing symbols; none should be reused for another game update.
constexpr ptr kStage = 0x488940;
constexpr ptr kWait = 0x514d70;
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
    GameplayCalled = 9,
    WindowAttached = 10,
    WindowEvaluated = 11,
    InputDispatched = 12
};

groove::Buffer<4096> buffer;
std::atomic<u32> lastCreatedStage{kUnknown};
// The SDK owns the opaque thread object and initializes its TLS.
alignas(0x1000) unsigned char writerStack[0x10000]{};
alignas(0x1000) unsigned char writerThreadStorage[0x1000]{};
bool writerStarted{};
void writerMain(void*);
u64 session{}, reportedLoss{};

bool sdReady = false;
bool sdMounted = false;
char storedSessionHeader[256]{};
int storedSessionHeaderLength{};
u64 dequeued{}, sdBatches{}, sdFailures{};

void reportPipeline(const char* phase);
constexpr const char* kSdMount = "grooverec";
constexpr const char* kSdFolder = "grooverec:/Orochi";
constexpr const char* kSdLog = "grooverec:/Orochi/groove-recorder.log";

void diagnostic(const char* message);

// One writer at a time: initialization hands off to the SDK thread.
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
        if (!written) (void)nn::fs::SetFileSize(file, fileSize);
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
        "GROOVE_DIAG pipeline phase=%s session=%llu queued=%llu dropped=%llu dequeued=%llu sd_batches=%llu sd_failures=%llu\n",
        phase, (unsigned long long)session,
        (unsigned long long)buffer.accepted(), (unsigned long long)buffer.dropped(),
        (unsigned long long)dequeued, (unsigned long long)sdBatches, (unsigned long long)sdFailures);
    if (size > 0 && size < static_cast<int>(sizeof(line))) {
        if (!appendFile(line, size)) ++sdFailures;
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

// The pinned target's fields are read as native words without aliasing its objects.
s32 nativeWord(const void* object, unsigned offset) {
    s32 value;
    __builtin_memcpy(&value, static_cast<const unsigned char*>(object) + offset, sizeof(value));
    return value;
}

void recordWindow(Kind kind, const void* window, s32 inputId, s32 detail, s32 relative) {
    buffer.push({0, hk::svc::getSystemTick(), kind,
                 lastCreatedStage.load(std::memory_order_relaxed), inputId,
                 static_cast<u32>(relative), detail,
                 {nativeWord(window, 0x24), nativeWord(window, 0x28),
                  nativeWord(window, 0x2c), nativeWord(window, 0x30)}});
}

HkTrampoline attachWindowHook = [](TrampolineStatic(), void* window, void* manager) -> void {
    orig(window, manager);
    recordWindow(WindowAttached, window, nativeWord(window, 0x10),
                 nativeWord(window, 0x44), nativeWord(window, 0x34));
};

HkTrampoline evaluateWindowHook = [](TrampolineStatic(), void* window, s32 inputId,
                                      s32* relativeOut) -> s32 {
    const bool matches = nativeWord(window, 0x10) == inputId;
    const s32 relative = matches ? nativeWord(window, 0x34) : 0;
    const s32 result = orig(window, inputId, relativeOut);
    // Mismatched IDs return before the original computes effective thresholds.
    if (matches) recordWindow(WindowEvaluated, window, inputId, result, relative);
    return result;
};

HkTrampoline dispatchInputHook = [](TrampolineStatic(), void* scene, s32 inputId,
                                     s32 argument, s32 group) -> u32 {
    const u32 dispatched = orig(scene, inputId, argument, group);
    buffer.push({0, hk::svc::getSystemTick(), InputDispatched,
                 lastCreatedStage.load(std::memory_order_relaxed), inputId,
                 0, argument, {group, dispatched}});
    return dispatched;
};

#include "groove_gameplay_hooks.inc"

void drain() {
    static char packet[48 * 192];
    static int used = 0;
    if (storedSessionHeaderLength > 0) {
        if (!appendFile(storedSessionHeader, storedSessionHeaderLength)) {
            ++sdFailures;
            return;
        }
        storedSessionHeaderLength = 0;
    }
    if (used == 0) {
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
    }
    if (used > 0) {
        if (!appendFile(packet, used)) {
            ++sdFailures;
            return;
        }
        ++sdBatches;
        used = 0;
    }
    const u64 loss = buffer.dropped();
    if (loss != reportedLoss) {
        char line[96];
        const int size = std::snprintf(line, sizeof(line), "GROOVE_LOST %llu %llu\n",
            (unsigned long long)session, (unsigned long long)loss);
        if (size > 0 && size < static_cast<int>(sizeof(line)) && appendFile(line, size))
            reportedLoss = loss;
    }
}

void writerMain(void*) {
    for (unsigned poll = 0;; ++poll) {
        hk::svc::SleepThread(100000000);
        drain();
        if (poll == 0 || poll % 50 == 0) reportPipeline("writer");
    }
}

HkTrampoline initHook = [](TrampolineStatic(), u64* argument) -> void {
    if (!sdReady) initSdLogging();
    orig(argument);
    if (sdReady && !writerStarted) {
        auto* thread = reinterpret_cast<nn::os::ThreadType*>(writerThreadStorage);
        // The pinned SDK adds 28 before svcCreateThread. A literal 44 here
        // becomes kernel priority 72 and aborts with InvalidPriority.
        constexpr int writerSdkPriority = 44 - 28;
        writerStarted = nn::os::CreateThread(thread, writerMain, nullptr, writerStack,
                                             sizeof(writerStack), writerSdkPriority, 0).IsSuccess();
        if (writerStarted) nn::os::StartThread(thread);
        else diagnostic("GROOVE_DIAG writer_create_failed\n");
    }
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
    const unsigned stage = installChecked(module, stageHook, kStage, 0xa9bb7bfd);
    const unsigned wait = installChecked(module, waitHook, kWait, 0xb9427808);
    const unsigned sfx = installChecked(module, sfxHook, kScheduleSfx, 0xfc190fec);
    const unsigned bgm = installChecked(module, bgmHook, kStartBgm, 0x6dba23e9);
    const unsigned subscene = installChecked(module, subSceneHook, kInitSubScene, 0x52800708);
    const unsigned cues = installChecked(module, cuesHook, kEnableCues, 0xa9bd7bfd);
    const unsigned threads = installChecked(module, appendThreadHook, kAppendThread, 0xf8408c08);
    unsigned hoop = 0;
    const unsigned gameplay = installGameplayHooks(module, hoop);
    const unsigned attached = installChecked(module, attachWindowHook, 0x12dd60, 0xfc1d0fe8);
    const unsigned evaluated = installChecked(module, evaluateWindowHook, 0x12e180, 0xb9401008);
    const unsigned dispatched = installChecked(module, dispatchInputHook, 0x12a690, 0xa9bd7bfd);
    char header[256];
    const int size = std::snprintf(header, sizeof(header),
        "GROOVE_SESSION3 %llu %llu %u %u %u %u %u %u %u %u %u\n"
        "GROOVE_DIAG native_hooks attached=%u evaluated=%u dispatched=%u\n",
        (unsigned long long)session,
        (unsigned long long)hk::svc::getSystemTickFrequency(),
        stage, wait, hoop, sfx, bgm, subscene, cues, threads, gameplay,
        attached, evaluated, dispatched);
    if (size > 0 && size < static_cast<int>(sizeof(header))) {
        emit(header, size);
        __builtin_memcpy(storedSessionHeader, header, size);
        storedSessionHeaderLength = size;
    }
    if (!installChecked(module, initHook, 0x50cba0, 0xa9bd7bfd))
        diagnostic("GROOVE_DIAG sd_mount_hook_failed\n");
}
