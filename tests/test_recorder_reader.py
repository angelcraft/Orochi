import unittest
from tools.read_groove_recorder import SUBSCENES, decode


class ReaderTests(unittest.TestCase):
    def test_native_input_trace_preserves_original_codes_and_order(self):
        attached, evaluated, dispatched = list(decode([
            "GROOVE_SESSION3 44 100 1 1 1 1 1 1 1 1 84\n",
            "GROOVE_NATIVE 44 1 100 10 10 0 3 -960 -28 -12 13 31\n",
            "GROOVE_NATIVE 44 2 180 10 11 0 2 -20 -28 -12 13 31\n",
            "GROOVE_NATIVE 44 3 181 10 12 0 7 0 3 1 0 0\n",
        ]))
        self.assertEqual([r["sequence"] for r in (attached, evaluated, dispatched)], [1, 2, 3])
        self.assertEqual(attached["main_offset"], "0x12dd60")
        self.assertEqual(attached["parameters"], {
            "logical_input_id": 0, "group": 3, "relative_ticks": -960,
            "effective_thresholds": [-28, -12, 13, 31],
        })
        self.assertEqual(evaluated["parameters"]["admission_code"], 2)
        self.assertEqual(evaluated["seconds_from_first_record"], 0.8)
        self.assertEqual(dispatched["parameters"]["dispatcher_result"], 1)
        for event in (attached, evaluated, dispatched):
            self.assertIsNone(event["judgement"])
            self.assertIsNone(event["musical_beat"])
            self.assertIsNone(event["player_input"])

    def test_window_identity_rearm_gaps_and_dispatch_context(self):
        records = decode([
            "GROOVE_SESSION3 44 100 1 1 1 1 1 1 1 1 84\n",
            "GROOVE_ACTION 44 1 100 10 54 20 1 0 0 0\n",
            "GROOVE_NATIVE2 44 2 101 10 10 0 3 -960 -100 -75 75 100 77\n",
            "GROOVE_NATIVE2 44 3 102 10 13 0 52 0 -100 -75 75 100 77\n",
            "GROOVE_NATIVE2 44 4 103 10 11 0 1 20 -100 -75 75 100 77\n",
            "GROOVE_NATIVE2 44 5 104 10 12 0 7 0 3 1 0 0 0\n",
            "GROOVE_NATIVE2 44 6 105 10 14 0 480 -460 -100 -75 75 100 77\n",
            "GROOVE_NATIVE2 44 7 106 10 11 0 0 -200 -100 -75 75 100 77\n",
            "GROOVE_NATIVE2 44 9 107 10 11 0 0 -200 -100 -75 75 100 77\n",
        ])
        action, attached, changed, evaluated, dispatched, rearmed, next_eval, after_gap = [
            next(records) for _ in range(8)
        ]
        self.assertEqual(attached["correlation"]["previous_gameplay_sequence_in_stage"], action["sequence"])
        self.assertEqual(changed["parameters"]["flags_before"], 4)
        self.assertEqual(changed["parameters"]["flags_after"], 6)
        self.assertEqual(evaluated["correlation"]["window_lifetime_start_sequence"], 2)
        self.assertEqual(dispatched["correlation"]["preceding_evaluations_since_previous_dispatch_for_id"], 1)
        self.assertEqual(next_eval["correlation"]["window_lifetime_start_sequence"], rearmed["sequence"])
        self.assertIsNone(after_gap["correlation"]["window_lifetime_start_sequence"])
        with self.assertRaises(StopIteration) as finished:
            next(records)
        stats = finished.exception.value[44]["native_input_statistics"]["10"]
        self.assertEqual(stats["attached_thresholds:-100,-75,75,100"], 1)
        self.assertEqual(stats["admission_code:0"], 2)
        self.assertEqual(stats["window_lifetime_unresolved"], 1)

    def test_corrupt_or_unterminated_records_are_not_decoded(self):
        records = decode([
            "GROOVE_NATIVE2 44 1 100 10 10 0 3 -960 -100 -75 75 100 18446744073709551615\r\n",
            "GROOVE_NATIVE2 44 2 101 10 11 0 1 0 -100 -75 75 100 18\x00\n",
            "GROOVE_NATIVE2 44 3 102 10 11 0 1 0 -100 -75 75 100 18"
            "GROOVE_SESSION3 46 100 1 1 1 1 1 1 1 1 84\n",
            "GROOVE_NATIVE2 44 4 103 10 11 0 1 0 -100 -75 75 100 18# session boundary\n",
            "GROOVE_SESSION3 45 100 1 1 1 1 1 1 1 1 84\n",
            "GROOVE_NATIVE2 45 1 110 10 10 0 3 -960 -100 -75 75 100 1844",
        ])
        first = next(records)
        self.assertEqual(first["correlation"]["window_token"], "ffffffffffffffff")
        with self.assertRaises(StopIteration) as finished:
            next(records)
        stats = finished.exception.value
        self.assertEqual(stats["_malformed_records"], 4)
        self.assertNotIn(46, stats)
        self.assertEqual(stats[45]["gameplay_hooks_installed"], 84)

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

    def test_gameplay_arguments_and_legacy_records_share_sequence(self):
        records = decode([
            "GROOVE_SESSION3 17 100 1 1 1 1 1 1 1 1 84\n",
            "GROOVE_REC2 17 1 100 1 14 0 4294967295 0\n",
            "GROOVE_ACTION 17 2 150 14 11 3 -2147483649 4294967296 1 0\n",
            "GROOVE_ACTION 17 3 200 14 70 27 1 1065353216 0 1\n",
            "GROOVE_ACTION 17 4 250 14 3 0 0 0 0 0\n",
        ])
        next(records)
        brake = next(records)
        self.assertEqual(brake["seconds_from_first_record"], 0.5)
        self.assertEqual(brake["main_offset"], "0x1608f0")
        self.assertEqual(brake["parameters"]["action"], "brake")
        self.assertEqual([a["value"] for a in brake["parameters"]["arguments"]],
                         [-2147483649, 4294967296, True])
        self.assertIsNone(brake["expected_input"])
        self.assertIsNone(brake["player_input"])
        self.assertIsNone(brake["judgement"])
        cue = next(records)
        self.assertEqual([a["value"] for a in cue["parameters"]["arguments"]],
                         [{"non_null": True}, {"ieee754_bits": "0x3f800000"},
                          {"non_null": False}, {"non_null": True}])
        self.assertEqual(next(records)["parameters"]["arguments"], [])
        with self.assertRaises(StopIteration) as finished:
            next(records)
        state = finished.exception.value[17]
        self.assertEqual(state["gameplay_hooks_installed"], 84)
        self.assertEqual(state["gameplay_commands_observed"], {11: 1, 70: 1, 3: 1})
        self.assertEqual(state["gaps"], 0)

    def test_session_without_hooks_does_not_invent_events(self):
        records = decode(["GROOVE_SESSION2 2 19200000 1 1 0 0 0 0 0 0\n"])
        with self.assertRaises(StopIteration) as finished:
            next(records)
        self.assertFalse(finished.exception.value[2]["hooks"]["sfx_scheduled"])
        self.assertEqual(finished.exception.value[2]["event_categories"], {})


if __name__ == "__main__":
    unittest.main()
