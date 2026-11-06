"""No proprietary Nintendo binaries: synthetic laboratory bundle tests."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from tests.test_npdm_one_svc import fixture
from tools.build_recorder_lab_zip import CONTENTS, NpdmError, create_bundle


class LabBundleTests(unittest.TestCase):
    def setUp(self):
        self.synthetic_nso = b"NSO0" + bytes(0x1000)

    def test_bundle_contents_and_exact_npdm_changes(self):
        files, report = create_bundle(fixture(), self.synthetic_nso)
        self.assertEqual(len(files), 4)
        self.assertIn(f"{CONTENTS}/subsdk1", files)
        self.assertIn(f"{CONTENTS}/main.npdm", files)
        self.assertEqual(files[f"{CONTENTS}/subsdk1"], self.synthetic_nso)
        self.assertNotEqual(files[f"{CONTENTS}/main.npdm"], fixture())
        self.assertEqual(json.loads(files["npdm-preflight.json"])["svc"], "0x74")
        self.assertTrue(report["requires_atmosphere_hardware_validation"])
        buffer = io.BytesIO()
        with ZipFile(buffer, "w") as z:
            for name, payload in files.items():
                z.writestr(name, payload)
        with ZipFile(buffer) as z:
            self.assertEqual(set(z.namelist()), set(files))
            self.assertEqual(z.read(f"{CONTENTS}/main.npdm"),
                             files[f"{CONTENTS}/main.npdm"])

    def test_invalid_module_is_rejected(self):
        with self.assertRaisesRegex(NpdmError, "plausible"):
            create_bundle(fixture(), b"INVALID")


if __name__ == "__main__":
    unittest.main()
