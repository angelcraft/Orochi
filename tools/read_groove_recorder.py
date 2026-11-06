"""Convert Groove debug output to JSONL and produce per-session coverage."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

TYPES = {1: ("stage_created", 0x488940, "created_stage_id"),
         2: ("wait_requested", 0x514D70, "duration_ticks"),
         3: ("hoop_called", 0x217960, "bubble_state")}
LINE = re.compile(r"\bGROOVE_(SESSION|REC|LOST) ((?:-?\d+ ?)+)")


def decode(lines):
    sessions = {}
    for line in lines:
        for match in LINE.finditer(line):
            tag = match[1]
            values = list(map(int, match[2].split()))
            if len(values) != {"SESSION": 5, "REC": 7, "LOST": 2}[tag]:
                continue
            sid, *args = values
            state = sessions.setdefault(sid, dict(stage_categories={}, last_sequence=0, gaps=0, dropped=0))
            if tag == "SESSION":
                state["clock_hz"], *hooks = args
                state["hooks"] = dict(zip(("stage_created", "wait_requested", "hoop_called"), map(bool, hooks)))
                continue
            if tag == "LOST":
                state["dropped"] = max(state["dropped"], args[0])
                continue
            seq, counter, kind, stage, value, tick = args
            name, offset, parameter = TYPES.get(kind, ("unknown", None, "raw_value"))
            if seq <= state["last_sequence"]:
                continue
            state["gaps"] += seq - state["last_sequence"] - 1
            state["last_sequence"] = seq
            stage_id = None if stage == 0xffffffff else stage
            counts = state["stage_categories"].setdefault(str(stage_id), Counter())
            counts[name] += 1
            yield dict(session=sid, sequence=seq, monotonic_counter=counter, type=name,
                       main_offset=hex(offset) if offset else None,
                       stage_context=stage_id, stage_provenance="factory_result" if kind == 1 else "last_factory_result",
                       thread_tick=None if tick == 0xffffffff else tick,
                       musical_beat=None, parameters={parameter: stage_id if kind == 1 else value})
    return sessions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("debug_log", type=Path)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("coverage", type=Path)
    args = parser.parse_args()
    with args.debug_log.open(encoding="utf8", errors="replace") as source, args.jsonl.open("x", encoding="utf8") as output:
        records = decode(source)
        while True:
            try:
                output.write(json.dumps(next(records)) + "\n")
            except StopIteration as done:
                report = done.value
                break
    with args.coverage.open("x", encoding="utf8") as output:
        json.dump(report, output, indent=2)


if __name__ == "__main__":
    main()
