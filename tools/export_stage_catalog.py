#!/usr/bin/env python3
"""Export reproducible, *observed* stage scopes from Groove Recorder logs.

Stage IDs are the last StageFactory result, not proof of ownership of a cue.
Counter time is not musical time. This tool never guesses beats or judgements.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any

try:
    from .read_groove_recorder import decode
except ImportError:
    from read_groove_recorder import decode

FIELDNAMES = (
    "session", "segment", "stage_context", "stage_provenance", "sequence",
    "seconds_from_first_record", "type", "scene_name", "command_id", "scene_class",
    "action", "logical_input_id", "relative_ticks", "admission_code",
    "dispatcher_result", "window_token", "window_lifetime_start_sequence",
    "musical_beat"
)
CANDIDATE_TYPES = {
    "gameplay_called", "input_window_attached", "input_window_evaluated",
    "logical_input_dispatched", "input_window_state_changed",
    "input_window_rearmed", "sfx_scheduled", "bgm_requested",
    "subscene_init_requested", "subscene_cues_enabled"
}


def export(log_path: Path, output_dir: Path, stage_filter: int | None = None) -> dict[str, Any]:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Output directory must be empty; existing analyses are preserved")
    output_dir.mkdir(parents=True, exist_ok=True)

    segment_by_session: dict[int, int] = {}
    latest_stage: dict[int, int | None] = {}
    scopes: dict[tuple[int, int, int | None], dict[str, Any]] = {}
    streams = {}
    rows = []
    report = None
    try:
        with log_path.open(encoding="utf-8", errors="replace") as stream:
            decoded = decode(stream)
            while True:
                try:
                    event = next(decoded)
                except StopIteration as done:
                    report = done.value
                    break
                sid = event["session"]
                stage = event["stage_context"]
                if event["type"] == "stage_created":
                    segment_by_session[sid] = segment_by_session.get(sid, 0) + 1
                    latest_stage[sid] = stage
                segment = segment_by_session.get(sid, 0)
                # A global last-factory stage can change across threads. Preserve
                # the actual observed stage, even when it differs from this segment.
                key = (sid, segment, stage)
                if stage_filter is not None and stage != stage_filter:
                    continue
                if key not in scopes:
                    stage_label = "unknown" if stage is None else str(stage)
                    relative = f"sessions/{sid}/segment-{segment:04d}-stage-{stage_label}.jsonl"
                    scopes[key] = {
                        "session": sid, "segment": segment, "stage_context": stage,
                        "file": relative, "records": 0, "event_types": Counter(),
                        "gameplay_actions": Counter(), "first_seconds": None,
                        "last_seconds": None, "context_mismatch_events": 0,
                    }
                    destination = output_dir / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    streams[key] = destination.open("x", encoding="utf-8")
                item = scopes[key]
                if latest_stage.get(sid) != stage and event["type"] != "stage_created":
                    item["context_mismatch_events"] += 1
                item["records"] += 1
                item["event_types"][event["type"]] += 1
                if event["type"] == "gameplay_called":
                    p = event["parameters"]
                    action = p.get("scene_class", "unknown") + "." + p.get("action", "unknown")
                    item["gameplay_actions"][action] += 1
                seconds = event.get("seconds_from_first_record")
                if item["first_seconds"] is None:
                    item["first_seconds"] = seconds
                item["last_seconds"] = seconds
                streams[key].write(json.dumps(event, ensure_ascii=False) + "\n")

                if event["type"] in CANDIDATE_TYPES:
                    p = event["parameters"]
                    corr = event.get("correlation") or {}
                    rows.append({
                        "session": sid, "segment": segment, "stage_context": stage,
                        "stage_provenance": event["stage_provenance"],
                        "sequence": event["sequence"],
                        "seconds_from_first_record": seconds,
                        "type": event["type"], "scene_name": p.get("scene_name"),
                        "command_id": p.get("command_id"),
                        "scene_class": p.get("scene_class"), "action": p.get("action"),
                        "logical_input_id": p.get("logical_input_id"),
                        "relative_ticks": p.get("relative_ticks"),
                        "admission_code": p.get("admission_code"),
                        "dispatcher_result": p.get("dispatcher_result"),
                        "window_token": corr.get("window_token"),
                        "window_lifetime_start_sequence": corr.get("window_lifetime_start_sequence"),
                        "musical_beat": None,
                    })
    finally:
        for handle in streams.values():
            handle.close()

    with (output_dir / "observations.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    ordered = [scopes[k] for k in sorted(scopes, key=lambda x: (x[0], x[1], -1 if x[2] is None else x[2]))]
    index = {
        "format": "groove-recorder-stage-catalog-v1",
        "source_file": log_path.name,
        "stage_filter": stage_filter,
        "stage_attribution": "last StageFactory result; may be stale or from another thread",
        "segment_definition": "increases at each recorded stage_created event per session; not a proven playthrough",
        "time_basis": "monotonic seconds relative to first decoded event of each session, NOT beat time",
        "musical_beats_verified": False,
        "input_judgements_verified": False,
        "scopes": ordered,
        "decoder_report": report,
    }
    with (output_dir / "index.json").open("x", encoding="utf-8") as stream:
        json.dump(index, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="Original sdmc:/Orochi/groove-recorder.log")
    parser.add_argument("output_dir", type=Path, help="New or empty output directory")
    parser.add_argument("--stage", type=int, help="Only export observations carrying this stage context")
    args = parser.parse_args()
    try:
        report = export(args.log, args.output_dir, args.stage)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "scopes": len(report["scopes"]),
        "events": sum(x["records"] for x in report["scopes"]),
        "output": str(args.output_dir),
        "beats_verified": False,
    }, indent=2))


if __name__ == "__main__":
    main()
