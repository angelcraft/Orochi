#pragma once

#include <cstddef>
#include <cstdint>
#include <limits>

namespace groove {

// Keep the original boundary across retries, including failures to shrink.
class AppendState {
    std::int64_t repairOffset = -1;

    template <typename Resize>
    bool repair(Resize& resize) {
        if (repairOffset < 0) return true;
        if (!resize(repairOffset)) return false;
        repairOffset = -1;
        return true;
    }

public:
    template <typename GetSize, typename Resize, typename Write>
    bool append(int size, GetSize getSize, Resize resize, Write write) {
        if (size <= 0 || !repair(resize)) return false;
        std::int64_t end{};
        if (!getSize(end) || end < 0 || end > std::numeric_limits<std::int64_t>::max() - size)
            return false;

        repairOffset = end;
        if (resize(end + size) && write(end)) {
            repairOffset = -1;
            return true;
        }
        repair(resize);
        return false;
    }
};

template <std::size_t Lines, std::size_t LineSize>
class Packet {
    char bytes[Lines * LineSize]{};
    int used = 0;

public:
    bool empty() const { return used == 0; }

    // A failed formatter leaves the committed prefix and its length intact.
    template <typename Format>
    bool add(Format format) {
        if (sizeof(bytes) - used < LineSize) return false;
        const int size = format(bytes + used, LineSize);
        if (size <= 0 || static_cast<std::size_t>(size) >= LineSize || bytes[used + size - 1] != '\n')
            return false;
        used += size;
        return true;
    }

    template <typename Append>
    bool flush(Append append) {
        if (empty()) return true;
        if (!append(bytes, used)) return false;
        used = 0;
        return true;
    }
};

}
