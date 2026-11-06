#include "groove_recorder_buffer.h"
#include "groove_recorder_writer.h"
#include <cassert>
#include <cstdio>
#include <string>
#include <thread>

static void ringWrapAndFull() {
    groove::Buffer<2> buffer;
    groove::Event out{};
    assert(!buffer.pop(out));
    buffer.push({0, 10, 1, 2, 3, 4});
    buffer.push({0, 20, 2, 2, 7, 8});
    buffer.push({0, 30, 3, 2, 9, 10});
    assert(buffer.droppedFull() == 1 && buffer.droppedBusy() == 0);
    assert(buffer.pop(out) && out.sequence == 1 && out.threadTick == 4);
    buffer.push({0, 40, 1, 2, 11, 12});
    assert(buffer.pop(out) && out.sequence == 2 && out.value == 7);
    assert(buffer.pop(out) && out.sequence == 3 && out.counter == 40);
    for (unsigned index = 3; index < 42048; ++index) {
        buffer.push({0, index, 1, 2, 0, 0});
        assert(buffer.pop(out) && out.sequence == index + 1 && out.counter == index);
    }
    assert(!buffer.pop(out) && buffer.dropped() == 1 && buffer.accepted() == 42048);
}

static void competingProducers() {
    constexpr int count = 20000;
    groove::Buffer<64> buffer;
    std::atomic<int> finished{0};
    const auto produce = [&] {
        for (int i = 0; i < count; ++i) buffer.push({0, 0, 1, 0, i, 0});
        finished.fetch_add(1);
    };
    std::thread first(produce), second(produce);
    groove::Event out{};
    std::uint64_t read = 0;
    const auto consume = [&] {
        if (!buffer.pop(out)) return false;
        assert(out.sequence == ++read);
        return true;
    };
    while (finished.load() != 2) consume();
    first.join();
    second.join();
    while (consume()) {}
    assert(read == buffer.accepted());
    assert(read + buffer.droppedBusy() + buffer.droppedFull() == 2 * count);
}

static void recoverPartialAppendAndPacket() {
    groove::Packet<3, 12> packet;
    assert(packet.add([](char* dest, std::size_t size) { return std::snprintf(dest, size, "one\n"); }));
    assert(!packet.add([](char* dest, std::size_t size) { return std::snprintf(dest, size, "truncated payload\n"); }));
    assert(!packet.add([](char*, std::size_t) { return -1; }));
    assert(!packet.add([](char* dest, std::size_t size) { return std::snprintf(dest, size, "no newline"); }));
    assert(packet.add([](char* dest, std::size_t size) { return std::snprintf(dest, size, "two\n"); }));

    groove::AppendState append;
    std::string disk = "existing\n";
    bool failShrink = true;
    bool failWrite = true;
    int writes = 0;
    const auto flush = [&](const char* bytes, int count) {
        return append.append(count,
            [&](std::int64_t& end) { end = disk.size(); return true; },
            [&](std::int64_t end) {
                if (failShrink && end < static_cast<std::int64_t>(disk.size())) return false;
                disk.resize(end);
                return true;
            },
            [&](std::int64_t end) {
                ++writes;
                if (failWrite) {
                    disk.replace(end, 2, bytes, 2);
                    return false;
                }
                disk.replace(end, count, bytes, count);
                return true;
            });
    };
    assert(!packet.flush(flush) && writes == 1 && !packet.empty());
    assert(!packet.flush(flush) && writes == 1 && !packet.empty());
    failShrink = failWrite = false;
    assert(packet.flush(flush) && writes == 2 && packet.empty());
    assert(disk == "existing\none\ntwo\n");
    assert(packet.flush(flush) && writes == 2);
}

int main() {
    ringWrapAndFull();
    competingProducers();
    recoverPartialAppendAndPacket();
    std::puts("Recorder ring, contention, serialization and retry tests passed");
}
