"""Decode Groove Recorder v1/v2/v3 logs to JSONL and coverage JSON.

A shared engine hook does not imply all actions or inputs were captured.
Every record retains provenance. "musical_beat" is intentionally unknown
until the game's tempo clock and thread timing have been verified.
"""
import argparse
from collections import Counter, OrderedDict
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
TAG = re.compile(r"\bGROOVE_(SESSION3|SESSION2|SESSION|ACTION|NATIVE2|NATIVE|REC2|REC|LOST)\s+([-\d ]+)")
DIAG = re.compile(r"\bGROOVE_DIAG\s+([^\r\n]+)")
EXPECT = {"SESSION": 5, "SESSION2": 10, "REC": 7,
          "REC2": 8, "LOST": 2, "SESSION3": 11, "ACTION": 10, "NATIVE": 12, "NATIVE2": 13}


def decode_argument(arg_type, raw):
    if arg_type.endswith("*"):
        return {"non_null": bool(raw)}
    if arg_type == "bool":
        return bool(raw)
    if arg_type == "float":
        return {"ieee754_bits": f"0x{raw & 0xffffffff:08x}"}
    return raw


def correlate_native(state, context, stage, seq, kind, parameters, token):
    stats = state.setdefault("native_input_statistics", {})
    counts = stats.setdefault(str(stage), Counter())
    counts["records"] += 1
    gameplay, windows, evaluations = context
    correlation = {"previous_gameplay_sequence_in_stage": gameplay.get(stage)}
    key = (stage, parameters["logical_input_id"])
    if kind == 12:
        counts[f"dispatcher_result:{parameters['dispatcher_result']}"] += 1
        correlation["preceding_evaluations_since_previous_dispatch_for_id"] = evaluations.pop(key, 0)
        return correlation

    if kind == 10:
        thresholds = ",".join(map(str, parameters["effective_thresholds"]))
        counts[f"attached_thresholds:{thresholds}"] += 1
    elif kind == 11:
        counts[f"admission_code:{parameters['admission_code']}"] += 1
        evaluations[key] = evaluations.get(key, 0) + 1
    elif kind == 13:
        before, after = parameters["flags_before"], parameters["flags_after"]
        counts[f"window_transition:{before}->{after}"] += 1
    elif kind == 14:
        counts["rearmed"] += 1

    if token is not None:
        if kind in (10, 14):
            windows[token] = seq
            windows.move_to_end(token)
            if len(windows) > 8192:
                windows.popitem(last=False)
                counts["window_context_evictions"] += 1
        lifetime = windows.get(token)
        if lifetime is not None:
            windows.move_to_end(token)
        else:
            counts["window_lifetime_unresolved"] += 1
        correlation.update(window_token=f"{token:016x}", window_lifetime_start_sequence=lifetime)
    return correlation


def decode(lines):
    sessions = {}
    diagnostics = []
    contexts = {}
    commands = None
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
                state["format"] = {"SESSION": 1, "SESSION2": 2, "SESSION3": 3}[tag]
                if tag == "SESSION3":
                    state["gameplay_hooks_installed"] = flags.pop()
                state["hooks"] = dict(zip(
                    HOOKS_V1 if tag == "SESSION" else HOOKS_V2,
                    map(bool, flags),
                ))
                continue
            if tag == "LOST":
                if args[0] > state["dropped"]:
                    contexts.pop(sid, None)
                    state["dropped"] = args[0]
                continue
            token = None
            if tag == "ACTION":
                seq, counter, stage, command_id, scene_id, *raw_args = args
                kind, value, thread_field, auxiliary = 9, command_id, 0xffffffff, None
            elif tag in ("NATIVE", "NATIVE2"):
                seq, counter, stage, kind, value, auxiliary, relative, *raw_args = args
                if tag == "NATIVE2":
                    token = raw_args.pop()
                    if not 0 <= token < 2**64:
                        continue
                if kind not in ((10, 11, 12, 13, 14) if tag == "NATIVE2" else (10, 11, 12)):
                    continue
                thread_field = 0xffffffff
            elif tag == "REC2":
                seq, counter, kind, stage, value, thread_field, auxiliary = args
            else:
                seq, counter, kind, stage, value, thread_field = args
                auxiliary = None
            if seq <= state["last_sequence"]:
                continue
            gap = seq - state["last_sequence"] - 1
            state["gaps"] += gap
            if gap:
                contexts.pop(sid, None)
            context = contexts.setdefault(sid, ({}, OrderedDict(), {}))
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
            if tag == "ACTION":
                if commands is None:
                    catalog = Path(__file__).with_name("groove_gameplay_catalog.json")
                    commands = {entry["id"]: entry for entry in
                                json.loads(catalog.read_text(encoding="utf-8"))["commands"]}
                command = commands.get(command_id)
                event_name = "gameplay_called"
                parameters = {"command_id": command_id, "remix_scene_id": None if scene_id < 0 else scene_id}
                if command and command["scene_id"] == scene_id:
                    offset = int(command["main_offset"], 16)
                    parameters.update(scene_class=command["scene"], action=command["action"])
                    parameters["arguments"] = [
                        {"type": arg_type, "value": decode_argument(arg_type, raw)}
                        for arg_type, raw in zip(command["arguments"], raw_args)
                    ]
                else:
                    parameters["raw_arguments"] = raw_args
                observed = state.setdefault("gameplay_commands_observed", Counter())
                observed[command_id] += 1
                context[0][stage_id] = seq
            correlation = None
            if tag in ("NATIVE", "NATIVE2"):
                if kind == 12:
                    event_name, offset = "logical_input_dispatched", 0x12A690
                    parameters = {"logical_input_id": value, "native_argument": auxiliary,
                                  "group": raw_args[0], "dispatcher_result": raw_args[1]}
                else:
                    event_name, offset, field = {
                        10: ("input_window_attached", 0x12DD60, "group"),
                        11: ("input_window_evaluated", 0x12E180, "admission_code"),
                        13: ("input_window_state_changed", 0x12DE60, "packed_flags"),
                        14: ("input_window_rearmed", 0x12E020, "delta_ticks"),
                    }[kind]
                    parameters = {"logical_input_id": value, "relative_ticks": relative,
                                  "effective_thresholds": raw_args, field: auxiliary}
                    if kind == 13:
                        parameters.update(flags_before=auxiliary & 7, flags_after=(auxiliary >> 3) & 7)
                correlation = correlate_native(state, context, stage_id, seq, kind, parameters, token)
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
                **({"correlation": correlation} if correlation is not None else {}),
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
