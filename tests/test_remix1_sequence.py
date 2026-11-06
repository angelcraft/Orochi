import unittest

from tools.remix1_sequence import compare_anchors, edited_events, event_rows


class RemixSequenceTests(unittest.TestCase):
    def test_anchor_identity_and_time(self):
        anchors = {"scene": {"beat": 0}, "cue": {"beat": 74}}
        rows = [{"datamodel": key, "type": "model", "beat": item["beat"]}
                for key, item in anchors.items()]
        self.assertEqual(set(compare_anchors({"entities": rows}, anchors)), set(anchors))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare_anchors({"entities": rows + [rows[0]]}, anchors)
        with self.assertRaisesRegex(ValueError, "missing"):
            compare_anchors({"entities": rows[:1]}, anchors)
        with self.assertRaisesRegex(ValueError, "native time"):
            compare_anchors({"entities": [rows[0], dict(rows[1], beat=75)]}, anchors)

    def test_only_target_ticks_can_change(self):
        source = event_rows({"ring": {"thread": "89_cues0", "pc_original": "0x3b2370",
                                      "action": "ring", "ticks": 35520}})
        result = edited_events(source, [dict(source[0], target_ticks=36000)])
        self.assertEqual(result[0]["target_ticks"], 36000)
        self.assertEqual(source[0]["target_ticks"], 35520)
        for changed in (dict(source[0], pc_original="0x0"),
                        dict(source[0], target_ticks=True),
                        dict(source[0], target_ticks=-1)):
            with self.assertRaises(ValueError):
                edited_events(source, [changed])
        with self.assertRaisesRegex(ValueError, "retain all"):
            edited_events(source, [])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            edited_events(source, source * 2)
