#pragma once
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace groove {
struct Event {
    std::uint64_t sequence;
    std::uint64_t counter;
    std::uint32_t kind;
    std::uint32_t stage;
    std::int32_t value;
    // Unknown raw thread field, not a verified musical tick.
    std::uint32_t threadTick;
    // Version 2 payload: e.g. SFX delay in ticks.
    std::int32_t auxiliary{};
    std::int64_t arguments[4]{};
    std::uint64_t windowToken{};
};

template <std::size_t Capacity>
class Buffer {
    static_assert(Capacity > 0);
    static_assert(std::atomic<std::uint64_t>::is_always_lock_free);
    std::atomic_flag lock = ATOMIC_FLAG_INIT;
    std::atomic<std::uint64_t> lostBusy{0}, lostFull{0};
    Event events[Capacity]{};
    std::size_t head{}, count{};
    std::atomic<std::uint64_t> sequence{0};

public:
    void push(Event event) {
        if (lock.test_and_set(std::memory_order_acquire)) {
            lostBusy.fetch_add(1, std::memory_order_relaxed);
            return;
        }
        if (count == Capacity) {
            lostFull.fetch_add(1, std::memory_order_relaxed);
        } else {
            event.sequence = ++sequence;
            events[(head + count) % Capacity] = event;
            ++count;
        }
        lock.clear(std::memory_order_release);
    }

    bool pop(Event& event) {
        if (lock.test_and_set(std::memory_order_acquire)) return false;
        const bool found = count != 0;
        if (found) {
            event = events[head];
            head = (head + 1) % Capacity;
            --count;
        }
        lock.clear(std::memory_order_release);
        return found;
    }

    std::uint64_t accepted() const { return sequence.load(std::memory_order_relaxed); }
    std::uint64_t droppedBusy() const { return lostBusy.load(std::memory_order_relaxed); }
    std::uint64_t droppedFull() const { return lostFull.load(std::memory_order_relaxed); }
    std::uint64_t dropped() const { return droppedBusy() + droppedFull(); }
};
}
