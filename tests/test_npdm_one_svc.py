"""Synthetic NPDM layout tests; no copyrighted game metadata is committed."""
import hashlib
import struct
import unittest
from unittest.mock import patch as mock

from tools.npdm_one_svc import NpdmError, PROGRAM_ID, patch

ACID_OFF, ACID_SIZE = 0x80, 0x380
ACI_OFF, ACI_SIZE = 0x400, 0x180
ACID_KAC_OFF, ACI_KAC_OFF = ACID_OFF + 0x2C0, ACI_OFF + 0x90
ORIGINAL_WORD = (4 << 29) | (1 << (5 + 19)) | 0xF
SVC74_BIT = 1 << (5 + 20)


def fixture() -> bytes:
    data = bytearray(0x600)
    data[:4] = b"META"
    struct.pack_into("<IIII", data, 0x70, ACI_OFF, ACI_SIZE, ACID_OFF, ACID_SIZE)
    data[ACI_OFF:ACI_OFF + 4] = b"ACI0"
    struct.pack_into("<Q", data, ACI_OFF + 0x10, PROGRAM_ID)
    struct.pack_into("<II", data, ACI_OFF + 0x30, 0x90, 4)
    data[ACID_OFF + 0x200:ACID_OFF + 0x204] = b"ACID"
    struct.pack_into("<QQ", data, ACID_OFF + 0x210, PROGRAM_ID, PROGRAM_ID)
    struct.pack_into("<II", data, ACID_OFF + 0x230, 0x2C0, 4)
    struct.pack_into("<I", data, ACI_KAC_OFF, ORIGINAL_WORD)
    struct.pack_into("<I", data, ACID_KAC_OFF, ORIGINAL_WORD)
    return bytes(data)


class NpdmOneSvcTests(unittest.TestCase):
    def test_exactly_two_descriptors_updated(self):
        source = fixture()
        patched, audit = patch(source)
        self.assertEqual(len(patched), len(source))
        self.assertEqual(struct.unpack_from("<I", patched, ACI_KAC_OFF)[0],
                         ORIGINAL_WORD | SVC74_BIT)
        self.assertEqual(struct.unpack_from("<I", patched, ACID_KAC_OFF)[0],
                         ORIGINAL_WORD | SVC74_BIT)
        allowed = set(range(ACI_KAC_OFF, ACI_KAC_OFF + 4)) | set(
            range(ACID_KAC_OFF, ACID_KAC_OFF + 4))
        changed = {i for i, (a, b) in enumerate(zip(source, patched)) if a != b}
        self.assertTrue(changed)
        self.assertTrue(changed <= allowed)
        self.assertEqual(len(audit["changed"]), 2)
        self.assertTrue(audit["signed_acid_modified"])

    def test_missing_group_fails_closed(self):
        source = bytearray(fixture())
        struct.pack_into("<I", source, ACID_KAC_OFF, 0xFFFFFFFF)
        with self.assertRaisesRegex(NpdmError, "ACID needs exactly one"):
            patch(bytes(source))

    def test_pinned_layout_appends_group_and_optionally_enables_sd(self):
        source = bytearray(0x654)
        source[:4] = b"META"
        source[0x470:0x474] = b"ACI0"
        source[0x280:0x284] = b"ACID"
        struct.pack_into("<IIII", source, 0x70, 0x470, 0x1e4, 0x80, 0x3e4)
        struct.pack_into("<Q", source, 0x480, PROGRAM_ID)
        struct.pack_into("<QQ", source, 0x290, PROGRAM_ID, PROGRAM_ID)
        struct.pack_into("<I", source, 0x284, 0x2e4)
        for offset in (0x2c4, 0x4b4):
            struct.pack_into("<Q", source, offset, 1 << 62)
        expected = source + bytes(4)
        for pos, new in ((0x74, 0x1e8), (0x7c, 0x3e8), (0x284, 0x2e8),
                         (0x2b4, 40), (0x4a4, 40), (0x464, 0x8200000f),
                         (0x654, 0x8200000f)):
            struct.pack_into("<I", expected, pos, new)
        recorder = bytearray(expected)
        recorder[0x2c6] = recorder[0x4b6] = 0x20
        with mock("tools.npdm_one_svc.ORIGINAL_NPDM_SHA256", hashlib.sha256(source).hexdigest()), \
             mock("tools.npdm_one_svc.CANDIDATE_NPDM_SHA256", hashlib.sha256(expected).hexdigest()), \
             mock("tools.npdm_one_svc.RECORDER_NPDM_SHA256", hashlib.sha256(recorder).hexdigest()):
            self.assertEqual(patch(bytes(source))[0], expected)
            candidate, report = patch(bytes(source), sd_access=True)
            self.assertEqual(candidate, recorder)
            self.assertEqual(set(report["filesystem_flags_updated"]), {"0x2c4", "0x4b4"})

    def test_sd_access_requires_pinned_npdm(self):
        with self.assertRaisesRegex(NpdmError, "exact original"):
            patch(fixture(), sd_access=True)

    def test_already_enabled_fails(self):
        source = bytearray(fixture())
        struct.pack_into("<I", source, ACI_KAC_OFF, ORIGINAL_WORD | SVC74_BIT)
        with self.assertRaisesRegex(NpdmError, "already set"):
            patch(bytes(source))

    def test_incorrect_title_refused(self):
        source = bytearray(fixture())
        struct.pack_into("<Q", source, ACI_OFF + 0x10, 123)
        with self.assertRaisesRegex(NpdmError, "Wrong title ID"):
            patch(bytes(source))

    def test_invalid_magic_refused(self):
        source = bytearray(fixture())
        source[:4] = b"NOPE"
        with self.assertRaisesRegex(NpdmError, "Expected META"):
            patch(bytes(source))

    def test_out_of_range_kac_refused(self):
        source = bytearray(fixture())
        struct.pack_into("<II", source, ACI_OFF + 0x30, 0x200, 4)
        with self.assertRaisesRegex(NpdmError, "extent"):
            patch(bytes(source))

    def test_overlapping_sections_refused(self):
        source = bytearray(fixture())
        struct.pack_into("<I", source, 0x70, 0x90)
        with self.assertRaisesRegex(NpdmError, "overlap"):
            patch(bytes(source))


if __name__ == "__main__":
    unittest.main()
