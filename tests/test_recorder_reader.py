import unittest
from tools.read_groove_recorder import SUBSCENES, decode


class ReaderTests(unittest.TestCase):
    def test_legacy_sessions_raw_fields_and_loss(self):
        records = decode([
            "prefix GROOVE_SESSION 44 19200000 1 1 1\n",
            "GROOVE_REC 44 1 50 1 14 0 4294967295\n",
            "GROOVE_REC 44 3 80 3 14 -1 8640\n",
            "GROOVE_LOST 44 2\n",
            "GROOVE_REC 45 1 90 2 4294967295 480 0\n",
        ])
        first = next(records)
        self.assertEqual(first["parameters"], {"created_stage_id": 14})
        hoop = next(records)
        self.assertEqual(hoop["raw_thread_field_0x278"], 8640)
        self.assertFalse(hoop["raw_thread_field_verified"])
        self.assertIsNone(hoop["musical_beat"])
        self.assertEqual(hoop["parameters"], {"bubble_state": -1})
        self.assertIsNone(next(records)["stage_context"])
        with self.assertRaises(StopIteration) as finished:
            next(records)
        self.assertEqual(finished.exception.value[44]["dropped"], 2)
        self.assertEqual(finished.exception.value[44]["gaps"], 1)

    def test_universal_cues_and_subscenes(self):
        self.assertEqual(len(SUBSCENES), 31)
        records = decode([
            "GROOVE_DIAG recorder_v2_entered\n",
            "GROOVE_SESSION2 99 100 1 1 1 1 1 1 1 1\n",
            "GROOVE_REC2 99 1 200 1 14 0 4294967295 0\n",
            "GROOVE_REC2 99 2 250 6 14 20 4294967295 123\n",
            "GROOVE_REC2 99 3 300 4 14 42 4294967295 480\n",
            "GROOVE_REC2 99 4 350 5 14 63 4294967295 960\n",
            "GROOVE_REC2 99 5 400 7 14 20 4294967295 0\n",
            "GROOVE_REC2 99 6 450 8 14 0 4294967295 0\n",
        ])
        items = []
        while True:
            try:
                items.append(next(records))
            except StopIteration as finished:
                state = finished.value
                break
        self.assertEqual(len(items), 6)
        self.assertEqual(items[1]["parameters"]["scene_name"], "Hoop Trundling")
        self.assertEqual(items[2]["parameters"], {"sfx_id": 42, "delay_ticks": 480})
        self.assertEqual(items[3]["parameters"], {"wavmark_id": 63, "delay_ticks": 960})
        self.assertEqual(items[3]["seconds_from_first_record"], 1.5)
        self.assertEqual(state[99]["event_categories"]["sfx_scheduled"], 1)
        self.assertEqual(state[99]["subscene_categories"]["20"]["subscene_init_requested"], 1)
        self.assertEqual(state["_diagnostics"], ["recorder_v2_entered"])

    def test_session_without_hooks_does_not_invent_events(self):
        records = decode(["GROOVE_SESSION2 2 19200000 1 1 0 0 0 0 0 0\n"])
        with self.assertRaises(StopIteration) as finished:
            next(records)
        self.assertFalse(finished.exception.value[2]["hooks"]["sfx_scheduled"])
        self.assertEqual(finished.exception.value[2]["event_categories"], {})


if __name__ == "__main__":
    unittest.main()
