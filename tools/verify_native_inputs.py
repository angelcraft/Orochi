"""Verify input evidence against the local Groove 1.0.0 Switch main NSO."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

SHA256 = "494c35e74dae893615980134f8be7673779f8d4b9eb9601e0f1b130d5ee1870e"
BUILD = "03ff4a3bec96bde3a2e37ce3aa4caa0cae8935a8000000000000000000000000"
GUARDS = {0x12A690: 0xA9BD7BFD, 0x12DD60: 0xFC1D0FE8, 0x12E180: 0xB9401008,
          0x12DE60: 0xA9BE7BFD, 0x12E020: 0xB9403408}
BRANCHES = {
    0x217538: 0x2182C0, 0x2182E8: 0x12F0F0,  # Hoop Trundling
    0x27D8A4: 0x27F010, 0x27F048: 0x12F0F0,  # Lightning Bolting
    0x12F164: 0x12DB30, 0x12F1AC: 0x12A670, 0x12A680: 0x12DD60,
    0x217360: 0x12A690, 0x2173C8: 0x12A690,
    0x27D68C: 0x12A690, 0x27D714: 0x12A690,
    0x18D8FC: 0x12F0F0, 0x18CE6C: 0x12A690, 0x12A6F0: 0x12E500,
    0x12E5A0: 0x12E180, 0x12E634: 0x12E180, 0x12E774: 0x12E180,
    0x12AF68: 0x12E390, 0x12F3BC: 0x12DE60, 0x12F4DC: 0x12E020,
    0x12AEAC: 0x515660, 0x12AF74: 0x12D930,
}
POINTERS = {
    0xD99F30: 0x217490, 0xD9AA48: 0x27D780,
    0xD225D8: 0x12F320, 0xD225F8: 0x2184B0, 0xD22600: 0x2185A0,
    0xD29830: 0x12F320, 0xD29850: 0x27F270, 0xD29858: 0x27F590,
}


# These witnesses pin the native accesses and return paths described in
# RECORDER_WINDOW_LIFETIME.md, in addition to the trampoline entry words.
LIFETIME_WORDS = {
    0x12DB4C: 0xB9004404, 0x12DB50: 0xB9001001, 0x12DB5C: 0xB9003408,
    0x12DB74: 0x3C824000,  # constructor initializes the recorded fields
    0x12DD7C: 0xF9000401, 0x12DD80: 0xB40003A1,
    0x12DE24: 0xA900CC15, 0x12F1B0: 0xF9402A60,  # publish, then reuse object
    0x12E1DC: 0xD63F0120, 0x12E1E8: 0x2D428400,
    0x12E274: 0xF8024009, 0x12E278: 0xB9403409,
    0x12E5A8: 0xB94042E8, 0x12E63C: 0xB9404308, 0x12E740: 0x3940E2C8,
    0x12E4C8: 0xD63F0100, 0x12E4CC: 0x3940E2C8, 0x12E3D0: 0xD63F0100,
    0x12DE80: 0xB9003408, 0x12DF38: 0xD63F0100, 0x12DF40: 0x3940E268,
    0x12E028: 0xB9003408, 0x12E030: 0x78039008, 0x12E034: 0xD65F03C0,
}


def verify(data):
    if hashlib.sha256(data).hexdigest() != SHA256 or data[0x40:0x60].hex() != BUILD:
        raise ValueError("Expected the unmodified Groove 1.0.0 Switch main NSO")
    import lz4.block

    flags, = struct.unpack_from("<I", data, 0xC)
    segments = []
    for index in range(3):
        off, base, size = struct.unpack_from("<III", data, 0x10 + 16 * index)
        if flags & (1 << index):
            stored, = struct.unpack_from("<I", data, 0x60 + 4 * index)
            segment = lz4.block.decompress(data[off:off + stored], uncompressed_size=size)
        else:
            segment = data[off:off + size]
        segments.append((base, segment))

    def word(address, fmt):
        for base, segment in segments:
            if base <= address and address + struct.calcsize(fmt) <= base + len(segment):
                return struct.unpack_from(fmt, segment, address - base)[0]
        raise ValueError(f"Address out of range {address:#x}")

    for addr, expected in GUARDS.items():
        if word(addr, "<I") != expected:
            raise ValueError(f"Hook guard mismatch at {addr:#x}")
    for addr, expected in LIFETIME_WORDS.items():
        if word(addr, "<I") != expected:
            raise ValueError(f"Window lifetime witness mismatch at {addr:#x}")
    for addr, expected in BRANCHES.items():
        insn = word(addr, "<I")
        displacement = ((insn & 0x03ffffff) ^ 0x02000000) - 0x02000000
        if insn & 0x7c000000 != 0x14000000 or addr + 4 * displacement != expected:
            raise ValueError(f"Branch mismatch at {addr:#x}")
    for addr, expected in POINTERS.items():
        if word(addr, "<Q") != expected:
            raise ValueError(f"Pointer mismatch at {addr:#x}")
    text = segments[0][1]
    callers = sum(
        (insn & 0x7c000000) == 0x14000000
        and 4 * (index + ((insn & 0x03ffffff) ^ 0x02000000) - 0x02000000) == 0x12A690
        for index, (insn,) in enumerate(struct.iter_unpack("<I", text))
    )
    return {"build_id": BUILD, "sha256": SHA256, "guards": len(GUARDS),
            "lifetime_words": len(LIFETIME_WORDS), "branches": len(BRANCHES), "pointers": len(POINTERS),
            "direct_dispatch_sites": callers}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.main.read_bytes()), indent=2))
