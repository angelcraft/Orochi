import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.export_stage_catalog import export


SESSION = "GROOVE_SESSION3 44 19200000 1 1 1 1 1 1 1 1 84\n"
LOG = "".join([
    SESSION,
    "GROOVE_REC2 44 1 100 1 89 0 4294967295 0\n",
    "GROOVE_ACTION 44 2 120 89 54 20 -1 0 0 0\n",
    "GROOVE_NATIVE2 44 3 140 89 10 0 5 -960 -120 -60 60 120 77\n",
    "GROOVE_NATIVE2 44 4 150 89 11 0 1 -2 -120 -60 60 120 77\n",
    "GROOVE_REC2 44 5 160 1 13 0 4294967295 0\n",
    "GROOVE_ACTION 44 6 170 13 36 12 0 0 0 0\n",
    "GROOVE_REC2 44 7 180 1 89 0 4294967295 0\n",
    "GROOVE_ACTION 44 8 190 89 54 20 -1 0 0 0\n",
])


class StageCatalogTests(unittest.TestCase):
    def test_stage_scopes_and_repeated_stage(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "input.log"
            src.write_text(LOG)
            out = root / "output"
            index = export(src, out)
            self.assertEqual([(s["stage_context"], s["segment"]) for s in index["scopes"]],
                             [(89, 1), (13, 2), (89, 3)])
            self.assertEqual(sum(s["records"] for s in index["scopes"]), 8)
            self.assertEqual(index["scopes"][0]["gameplay_actions"], {"SceneRing.hoop": 1})
            with (out / "observations.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 5)
            self.assertEqual([r["type"] for r in rows[:3]],
                             ["gameplay_called", "input_window_attached", "input_window_evaluated"])
            self.assertEqual(rows[2]["relative_ticks"], "-2")
            self.assertEqual(rows[2]["admission_code"], "1")
            self.assertEqual(rows[2]["window_token"], "000000000000004d")
            self.assertEqual({r["musical_beat"] for r in rows}, {""})
            self.assertFalse(index["musical_beats_verified"])
            self.assertTrue((out / index["scopes"][0]["file"]).exists())

    def test_filter_is_observed_stage_not_proven_cue_owner(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "input.log"
            src.write_text(LOG)
            out = root / "filtered"
            index = export(src, out, 89)
            self.assertEqual([(s["stage_context"], s["segment"]) for s in index["scopes"]],
                             [(89, 1), (89, 3)])
            self.assertEqual(index["stage_filter"], 89)
            self.assertIn("last StageFactory result", index["stage_attribution"])
            with self.assertRaises(ValueError):
                export(src, out, 89)

    def test_legacy_without_factory_is_kept_as_segment_zero(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "legacy.log"
            src.write_text("GROOVE_REC2 12 1 10 2 4294967295 480 4294967295 0\n")
            index = export(src, root / "output")
            self.assertEqual(len(index["scopes"]), 1)
            self.assertEqual(index["scopes"][0]["segment"], 0)
            self.assertIsNone(index["scopes"][0]["stage_context"])
            self.assertEqual(index["scopes"][0]["event_types"]["wait_requested"], 1)


if __name__ == "__main__":
    unittest.main()
