#!/usr/bin/env python3
"""Offline, strictly in-place NPDM svcMapProcessMemory capability audit/patch.

Accepts only an original Groove 1.0.0 main.npdm extracted by its owner.
Never changes ExeFS, never installs a patch, and never rewrites unrelated
permissions. An NPDM produced by this tool has a modified *signed* ACID
payload; Atmosphère and the Switch still must validate and load it.

Based on the META/ACI0/ACID offsets in switchbrew.org/wiki/NPDM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

PROGRAM_ID = 0x0100D9F01D474000
SVC = 0x74
SVC_GROUP = SVC // 24
SVC_BIT = SVC % 24
CAP_ID = 4
SVC_MASK_TAG = (1 << CAP_ID) - 1
MAX_BYTES = 1024 * 1024


class NpdmError(ValueError):
    """Refuse unrecognized layouts and unverified modifications."""


def u32(data: bytes, where: int) -> int:
    if where < 0 or where + 4 > len(data):
        raise NpdmError("Out-of-range 32-bit field")
    return struct.unpack_from("<I", data, where)[0]


def u64(data: bytes, where: int) -> int:
    if where < 0 or where + 8 > len(data):
        raise NpdmError("Out-of-range 64-bit field")
    return struct.unpack_from("<Q", data, where)[0]


def bounds(start: int, length: int, total: int, label: str) -> tuple[int, int]:
    if start < 0 or length < 0 or start > total or length > total - start:
        raise NpdmError(f"Invalid {label} extent")
    return (start, start + length)


def kac_words(
    data: bytes, *, section_start: int, section_size: int, kac_offset_field: int,
    label: str,
) -> list[tuple[int, int]]:
    sec_start, sec_end = bounds(section_start, section_size, len(data), label)
    if sec_end - sec_start < kac_offset_field + 8:
        raise NpdmError(f"{label} header truncated")
    rel = u32(data, sec_start + kac_offset_field)
    size = u32(data, sec_start + kac_offset_field + 4)
    if size == 0 or size % 4 or rel % 4:
        raise NpdmError(f"{label} invalid KAC word alignment")
    if rel < kac_offset_field + 8:
        raise NpdmError(f"{label} KAC overlaps header")
    first, end = bounds(sec_start + rel, size, sec_end, label + " KAC")
    return [(pos, u32(data, pos)) for pos in range(first, end, 4)]


def svc_words(entries: list[tuple[int, int]], label: str) -> tuple[int, int]:
    found: list[tuple[int, int]] = []
    for offset, value in entries:
        if (value & 0x1F) == SVC_MASK_TAG and (value >> 29) == SVC_GROUP:
            found.append((offset, value))
    if len(found) != 1:
        raise NpdmError(
            f"{label} needs exactly one existing svc group {SVC_GROUP} descriptor; "
            f"found {len(found)}. Refusing to relocate KAC."
        )
    return found[0]


def patch(original: bytes) -> tuple[bytes, dict]:
    if len(original) < 0x80 or len(original) > MAX_BYTES:
        raise NpdmError("NPDM size not plausible")
    if original[:4] != b"META":
        raise NpdmError("Expected META header")
    aci_off, aci_size = u32(original, 0x70), u32(original, 0x74)
    acid_off, acid_size = u32(original, 0x78), u32(original, 0x7C)
    if aci_off % 0x10 or acid_off % 0x10:
        raise NpdmError("Unaligned section offsets")
    aci_a, aci_b = bounds(aci_off, aci_size, len(original), "ACI0")
    acid_a, acid_b = bounds(acid_off, acid_size, len(original), "ACID")
    if aci_a < 0x80 or acid_a < 0x80 or not (aci_b <= acid_a or acid_b <= aci_a):
        raise NpdmError("NPDM section overlap")
    if original[aci_a:aci_a + 4] != b"ACI0":
        raise NpdmError("Expected ACI0 header")
    if acid_size < 0x240 or original[acid_a + 0x200:acid_a + 0x204] != b"ACID":
        raise NpdmError("Expected Switch 1 ACID header")
    actual_id = u64(original, aci_a + 0x10)
    if actual_id != PROGRAM_ID:
        raise NpdmError(f"Wrong title ID {actual_id:016x}; expected {PROGRAM_ID:016x}")
    minimum, maximum = u64(original, acid_a + 0x210), u64(original, acid_a + 0x218)
    if not minimum <= actual_id <= maximum:
        raise NpdmError("ACI0 title ID outside ACID program ID range")
    aci = svc_words(kac_words(
        original, section_start=aci_off, section_size=aci_size,
        kac_offset_field=0x30, label="ACI0"), "ACI0")
    acid = svc_words(kac_words(
        original, section_start=acid_off, section_size=acid_size,
        kac_offset_field=0x230, label="ACID"), "ACID")
    # Preserve the original ACI0 ⊆ ACID syscall restriction relationship.
    syscall_mask = ((1 << 24) - 1) << 5
    if (aci[1] & syscall_mask) & ~(acid[1] & syscall_mask):
        raise NpdmError("Original ACI0 requests syscalls outside ACID limits")
    bit = 1 << (5 + SVC_BIT)
    if (aci[1] & bit) or (acid[1] & bit):
        raise NpdmError("0x74 is already set in ACI0 or ACID: original NPDM was not expected")
    updated = bytearray(original)
    changed = []
    for label, (offset, old) in (("ACI0", aci), ("ACID", acid)):
        new = old | bit
        struct.pack_into("<I", updated, offset, new)
        changed.append({"section": label, "offset": f"0x{offset:x}",
                        "old_word": f"0x{old:08x}", "new_word": f"0x{new:08x}"})
    patched = bytes(updated)
    delta = [p for p, (a, b) in enumerate(zip(original, patched)) if a != b]
    permitted = {off for off, _ in (aci, acid) for off in range(off, off + 4)}
    if not delta or not set(delta) <= permitted or len(patched) != len(original):
        raise NpdmError("Unexpected bytes changed")
    for offset, word in (aci, acid):
        if (u32(patched, offset) >> 29) != SVC_GROUP:
            raise NpdmError("KAC svc group unexpectedly changed")
        if (u32(patched, offset) & bit) == 0:
            raise NpdmError("SVC bit not written")
    report = {
        "status": "static_candidate_only",
        "title_id": f"{PROGRAM_ID:016x}",
        "svc": f"0x{SVC:x}",
        "original_sha256": hashlib.sha256(original).hexdigest(),
        "candidate_sha256": hashlib.sha256(patched).hexdigest(),
        "original_length": len(original),
        "signed_acid_modified": True,
        "requires_atmosphere_hardware_validation": True,
        "changed": changed,
        "changed_byte_offsets": [f"0x{p:x}" for p in delta],
        "notes": [
            "No ACI0/ACID length, service, filesystem or unrelated capability altered.",
            "This does not sign ACID. The candidate may be rejected by loader or kernel.",
            "Never share the candidate NPDM or original extracted files publicly.",
            "Use only with original Groove 1.0.0 extracted from your own installation."
        ],
    }
    return patched, report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original", type=Path, help="Owner-extracted original main.npdm")
    p.add_argument("--output", type=Path, help="Write *local* experimental main.npdm")
    p.add_argument("--report", type=Path, help="Write JSON preflight manifest")
    a = p.parse_args()
    original = a.original.read_bytes()
    patched, report = patch(original)
    print(json.dumps(report, indent=2))
    if a.output:
        if a.output.resolve() == a.original.resolve() or a.output.exists():
            p.error("Refusing to overwrite original or an existing file")
        a.output.write_bytes(patched)
    if a.report:
        if a.report.exists():
            p.error("Refusing to overwrite report")
        a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
