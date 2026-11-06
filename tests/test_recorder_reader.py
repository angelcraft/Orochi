import unittest
from tools.read_groove_recorder import decode


class ReaderTests(unittest.TestCase):
    def test_sessions_raw_fields_and_loss(self):
        records = decode([
            "prefix GROOVE_SESSION 44 19200000 1 1 1\n",
            "GROOVE_REC 44 1 50 1 14 0 4294967295\n",
            "GROOVE_REC 44 3 80 3 14 -1 8640\n",
            "GROOVE_LOST 44 2\n",
            "GROOVE_REC 45 1 90 2 4294967295 480 0\n",
        ])
        self.assertEqual(next(records)["parameters"], {"created_stage_id": 14})
        hoop = next(records)
        self.assertEqual(hoop["thread_tick"], 8640)
        self.assertIsNone(hoop["musical_beat"])
        self.assertEqual(hoop["parameters"], {"bubble_state": -1})
        self.assertIsNone(next(records)["stage_context"])
        with self.assertRaises(StopIteration) as finished:
            next(records)
        self.assertEqual(finished.exception.value[44]["dropped"], 2)
        self.assertEqual(finished.exception.value[44]["gaps"], 1)
