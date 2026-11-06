#include "groove_recorder_buffer.h"
#include <cassert>
int main() {
    groove::Buffer<2> buffer;
    groove::Event out{};
    assert(!buffer.pop(out));
    buffer.push({0, 10, 1, 2, 3, 4});
    buffer.push({0, 20, 2, 2, 7, 8});
    buffer.push({0, 30, 3, 2, 9, 10});
    assert(buffer.dropped() == 1);
    assert(buffer.pop(out) && out.sequence == 1 && out.threadTick == 4);
    buffer.push({0, 40, 1, 2, 11, 12});
    assert(buffer.pop(out) && out.sequence == 2 && out.value == 7);
    assert(buffer.pop(out) && out.sequence == 3 && out.counter == 40);
    assert(!buffer.pop(out) && buffer.dropped() == 1);
}
