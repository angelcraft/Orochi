"""Decode Groove Recorder v1/v2 debug logs to JSONL and coverage JSON.

A shared engine hook does not imply all actions or inputs were captured.
Every record retains provenance. "musical_beat" is intentionally unknown
until the game's tempo clock and thread timing have been verified.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

HOOKS_V1 = ("stage_created", "wait_requested", "hoop_called")
HOOKS_V2 = HOOKS_V1 + (
    "sfx_scheduled", "bgm_requested", "subscene_init_requested",
    "subscene_cues_enabled", "thread_appended",
)
TYPES = {
    1: ("stage_created", 0x488940, "created_stage_id"),
    2: ("wait_requested", 0x514D70, "duration_ticks"),
    3: ("hoop_called", 0x217960, "bubble_state"),
    4: ("sfx_scheduled", 0x12BFF0, "sfx_id"),
    5: ("bgm_requested", 0x139140, "wavmark_id"),
    6: ("subscene_init_requested", 0x4D9DC0, "scene_id"),
    7: ("subscene_cues_enabled", 0x4DAA70, "scene_id"),
    8: ("thread_appended", 0x5153A0, None),
}
# StageRemix's Scene IDs, from Orochi include/aloha/Stage.h. These IDs are
# NOT the same thing as a StageFactory stage ID.
SUBSCENES = (
    "Germ Aerobics", "Synchro Wings", "Sweeper Star", "Stop 'n Go Stop",
    "High-Five Fever", "Slice N Dice Kitchen", "Crab Snacks",
    "Backup Spotlight", "Disc Dog", "Quick Hands", "Space Sentry",
    "Can Do", "Feeding the Beast", "Hop 'n Slide", "Flutter Speed",
    "Ribbit Rocket", "Sneezy Moon", "Brolly Good Show", "Fruit Flex",
    "Pop Don't Drop", "Hoop Trundling", "Hop Stop 'n Roll",
    "Soda Hop", "Spirit Slasher", "Football Dreams", "Yum-Bot Simulator",
    "Alien Alphabet", "A for Effort", "Lightning Bolting",
    "Wiper Bosses", "Deep Sea",
)
TAG = re.compile(r"\bGROOVE_(SESSION2|SESSION|REC2|REC|LOST)\s+([-\d ]+)")
DIAG = re.compile(r"\bGROOVE_DIAG\s+([^\r\n]+)")
EXPECT = {"SESSION": 5, "SESSION2": 10, "REC": 7,
          "REC2": 8, "LOST": 2}


def decode(lines):
    sessions = {}
    diagnostics = []
    for line in lines:
        diagnostic = DIAG.search(line)
        if diagnostic:
            diagnostics.append(diagnostic.group(1).strip())
        for match in TAG.finditer(line):
            tag = match[1]
            try:
                numbers = list(map(int, match[2].split()))
            except ValueError:
                continue
            if len(numbers) != EXPECT[tag]:
                continue
            sid, *args = numbers
            state = sessions.setdefault(sid, {
                "stage_categories": {},
                "subscene_categories": {},
                "event_categories": Counter(),
                "last_sequence": 0, "gaps": 0, "dropped": 0,
                "first_counter": None,
            })
            if tag.startswith("SESSION"):
                hz, *flags = args
                state["clock_hz"] = hz
                state["format"] = 2 if tag == "SESSION2" else 1
                state["hooks"] = dict(zip(
                    HOOKS_V2 if tag == "SESSION2" else HOOKS_V1,
                    map(bool, flags),
                ))
                continue
            if tag == "LOST":
                state["dropped"] = max(state["dropped"], args[0])
                continue
            if tag == "REC2":
                seq, counter, kind, stage, value, thread_field, auxiliary = args
            else:
                seq, counter, kind, stage, value, thread_field = args
                auxiliary = None
            if seq <= state["last_sequence"]:
                continue
            state["gaps"] += seq - state["last_sequence"] - 1
            state["last_sequence"] = seq
            if state["first_counter"] is None:
                state["first_counter"] = counter
            event_name, offset, param = TYPES.get(
                kind, ("unknown", None, "raw_value")
            )
            stage_id = None if stage == 0xffffffff else stage
            parameters = {}
            if param:
                parameters[param] = stage_id if kind == 1 else value
            if kind in (4, 5) and auxiliary is not None:
                parameters["delay_ticks"] = auxiliary
            if kind == 6 and auxiliary is not None:
                parameters["unresolved_argument"] = auxiliary
            if kind in (6, 7):
                parameters["scene_name"] = (
                    SUBSCENES[value] if 0 <= value < len(SUBSCENES) else None
                )
                context = str(value)
                scene_counts = state["subscene_categories"].setdefault(
                    context, Counter()
                )
                scene_counts[event_name] += 1
            counts = state["stage_categories"].setdefault(
                str(stage_id), Counter()
            )
            counts[event_name] += 1
            state["event_categories"][event_name] += 1
            hz = state.get("clock_hz")
            elapsed = (
                (counter - state["first_counter"]) / hz
                if isinstance(hz, int) and hz > 0 else None
            )
            yield {
                "session": sid, "sequence": seq,
                "monotonic_counter": counter,
                "seconds_from_first_record": elapsed,
                "type": event_name,
                "main_offset": hex(offset) if offset else None,
                "stage_context": stage_id,
                "stage_provenance": (
                    "factory_result" if kind == 1 else "last_factory_result"
                ),
                "raw_thread_field_0x278": (
                    None if thread_field == 0xffffffff else thread_field
                ),
                "raw_thread_field_verified": False,
                "musical_beat": None,
                "expected_input": None,
                "player_input": None,
                "judgement": None,
                "parameters": parameters,
            }
    if diagnostics:
        sessions["_diagnostics"] = diagnostics
    return sessions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("debug_log", type=Path)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("coverage", type=Path)
    args = parser.parse_args()
    with args.debug_log.open(encoding="utf8", errors="replace") as source, \
         args.jsonl.open("x", encoding="utf8") as output:
        records = decode(source)
        while True:
            try:
                output.write(json.dumps(next(records), ensure_ascii=False) + "\n")
            except StopIteration as done:
                report = done.value
                break
    with args.coverage.open("x", encoding="utf8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
