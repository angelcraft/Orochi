"""Synthetic NPDM layout tests; no copyrighted game metadata is committed."""
import struct
import unittest

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
