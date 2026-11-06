"""No proprietary Nintendo binaries: synthetic laboratory bundle tests."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
from unittest.mock import patch

from tests.test_npdm_one_svc import fixture
from tools.build_recorder_lab_zip import BUILD_ID, CONTENTS, NpdmError, check_sd, create_bundle


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

    def test_sd_requires_atmosphere_and_preserves_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd = Path(tmp)
            with self.assertRaisesRegex(NpdmError, "raíz"):
                check_sd(sd)
            exefs = sd / CONTENTS
            exefs.mkdir(parents=True)
            self.assertEqual(check_sd(sd), [])
            for conflict in (exefs / "subsdk1", exefs / "main.npdm",
                             exefs / "subsdk0.stub", exefs.parent / "exefs.nsp"):
                conflict.write_bytes(b"keep")
                with self.assertRaisesRegex(NpdmError, conflict.name):
                    check_sd(sd)
                self.assertEqual(conflict.read_bytes(), b"keep")
                conflict.unlink()

    def test_sd_matches_shortened_build_ids_and_checks_patch_identity(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            sd = Path(tmp)
            ips = sd / "atmosphere" / "exefs_patches" / "hoop"
            ips.mkdir(parents=True)
            shortened = ips / (BUILD_ID[:40].upper() + ".ips")
            shortened.write_bytes(b"patch")
            with self.assertRaisesRegex(NpdmError, "IPS"):
                check_sd(sd)
            with patch("tools.build_recorder_lab_zip.PLUS240_SHA256",
                       hashlib.sha256(b"patch").hexdigest()):
                self.assertEqual(check_sd(sd), [shortened.relative_to(sd).as_posix()])
                shortened.with_name(BUILD_ID + ".ips").write_bytes(b"patch")
                with self.assertRaisesRegex(NpdmError, "varias copias"):
                    check_sd(sd)

    def test_sd_rejects_patch_targeting_recorder_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd = Path(tmp)
            ips = sd / "atmosphere" / "exefs_patches" / "module"
            ips.mkdir(parents=True)
            (ips / "aa.ips").write_bytes(b"patch")
            self.assertEqual(check_sd(sd), [])
            with self.assertRaisesRegex(NpdmError, "IPS"):
                check_sd(sd, {"aa".ljust(64, "0")})


if __name__ == "__main__":
    unittest.main()
