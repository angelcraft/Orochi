"""Build an editable Remix 1 sequence from a local Groove 1.0.0 NSO."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from .read_groove_recorder import decode
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from read_groove_recorder import decode

FORMAT = "groove-remix1-sequence-v1"


def compare_anchors(project, expected):
    seen = {}
    for entity in project["entities"]:
        ident = entity.get("datamodel")
        if ident not in expected:
            continue
        if ident in seen or entity.get("type") != "model":
            raise ValueError(f"Invalid or duplicate RHRE anchor: {ident}")
        if entity.get("beat") != expected[ident]["beat"]:
            raise ValueError(f"RHRE anchor differs from native time: {ident}")
        seen[ident] = entity
    if seen.keys() != expected.keys():
        raise ValueError("RHRE project is missing native cues or scene anchors")
    return seen


def edited_events(original, requested):
    by_id = {event["id"]: event for event in original}
    seen = set()
    result = []
    for row in requested:
        ident = row["id"]
        if ident not in by_id or ident in seen:
            raise ValueError(f"Unknown or duplicate edit identity: {ident}")
        seen.add(ident)
        baseline = by_id[ident]
        if {k: v for k, v in row.items() if k != "target_ticks"} != {
            k: v for k, v in baseline.items() if k != "target_ticks"
        }:
            raise ValueError(f"Native baseline fields were changed: {ident}")
        tick = row["target_ticks"]
        if type(tick) is not int or not 0 <= tick <= 512 * 480:
            raise ValueError(f"Invalid tick target: {ident}")
        result.append({**baseline, "target_ticks": tick})
    if seen != by_id.keys():
        raise ValueError("The native edit set must retain all events")
    return result


def event_rows(facts):
    return [
        {"id": ident, "thread": event["thread"], "pc_original": event["pc_original"],
         "action": event["action"], "original_ticks": event["ticks"], "target_ticks": event["ticks"]}
        for ident, event in facts.items()
    ]


def observations(path):
    # Stage context is only the most recent factory result. Keep timing and
    # identity as observations and never use them to fill native edit fields.
    sessions = {}
    with path.open(encoding="utf-8", errors="replace") as stream:
        for event in decode(stream):
            if event["stage_context"] == 89:
                stats = sessions.setdefault(str(event["session"]), Counter())
                stats[event["type"]] += 1
    return {"origin": "runtime_observation", "stage_context_filter": 89,
            "identity_join": None, "counts_by_session": sessions}


def research_backend(root):
    if not (root / "research/tools/export_switch_batch.py").is_file():
        raise ValueError("Expected the existing Switch Studio research checkout")
    sys.path.insert(0, str(root.resolve()))
    from research.tools import export_switch_batch, recover_switch_remix1
    return export_switch_batch, recover_switch_remix1


def snapshot(main, rhref, trace, backend, recovery):
    report = recovery.recover(main)
    _, image = recovery.load_original(main)
    cues, facts, scenes = backend.native_facts(image)
    project, audio = backend.read_project(rhref)
    anchors = compare_anchors(project, {**facts, **scenes})
    reference = json.loads(backend.FIXTURE.read_text(encoding="utf-8"))
    mapping = backend.convert(image, {"build_id": report["build_id"],
                                      "sha256": report["source_sha256"]},
                              reference, rhref, rhref)
    return {
        "format": FORMAT, "stage_id": 89, "title_id": "0100d9f01d474000", "version": "1.0.0",
        "build_id": report["build_id"], "source_sha256": report["source_sha256"],
        "program": {"threads": report["threads"], "control": report["control"],
                    "music": report["music"], "ticks_per_beat": report["ticks_per_beat"]},
        "rhref": {"native_anchors": anchors, "audio_sha256": audio,
                  "music_start_seconds": project.get("musicStartSec"),
                  "tempo_track": project.get("trackers", {}).get("tempos"),
                  "pattern_correspondences": mapping["events"],
                  "mapping_semantics": mapping["mapping_semantics"]},
        "capabilities": backend.capabilities(image, cues),
        "edits": event_rows(facts),
        "observations": observations(trace) if trace else None,
    }


def export(main, document, destination, existing, backend, recovery):
    source, image = recovery.load_original(main)
    if (document.get("format"), document.get("stage_id"), document.get("title_id"),
        document.get("version"), document.get("build_id"), document.get("source_sha256")) != (
        FORMAT, 89, "0100d9f01d474000", "1.0.0", source["build_id"], source["sha256"]
    ):
        raise ValueError("Sequence version or original NSO identity mismatch")
    _, facts, _ = backend.native_facts(image)
    events = edited_events(event_rows(facts), document["edits"])
    patch, rollback, report = backend.plan(image, source, {
        "format": "groove-remix1-native-edit-v1", "title_id": "0100d9f01d474000",
        "version": "1.0.0", "build_id": source["build_id"], "source_sha256": source["sha256"],
        "events": events,
    })
    report["existing_ips_checks"] = backend.check_conflicts(patch, existing)
    if any(row["status"] == "conflict" for row in report["existing_ips_checks"]):
        raise ValueError("Conflicting IPS; output was not created")
    with ZipFile(destination, "x", ZIP_DEFLATED) as archive:
        archive.writestr(f"atmosphere/exefs_patches/groove-remix1-sequence/{source['build_id']}.ips", patch)
        archive.writestr("rollback-offline-only.ips", rollback)
        archive.writestr("verification.json", json.dumps(report, indent=2))
        archive.writestr("README.txt", "Groove Switch 1.0.0. Enable only this patch for these instructions. "
                         "Remove it to disable. Never install the offline rollback IPS. "
                         "This export was verified offline.\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, required=True)
    sub = parser.add_subparsers(dest="operation", required=True)
    read = sub.add_parser("snapshot")
    read.add_argument("main", type=Path)
    read.add_argument("rhref", type=Path)
    read.add_argument("output", type=Path)
    read.add_argument("--trace", type=Path)
    write = sub.add_parser("export")
    write.add_argument("main", type=Path)
    write.add_argument("sequence", type=Path)
    write.add_argument("output", type=Path)
    write.add_argument("--existing-ips", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        backend, recovery = research_backend(args.research_root)
        if args.operation == "snapshot":
            document = snapshot(args.main, args.rhref, args.trace, backend, recovery)
            with args.output.open("x", encoding="utf-8") as output:
                json.dump(document, output, ensure_ascii=False, indent=2)
        else:
            report = export(args.main, json.loads(args.sequence.read_text(encoding="utf-8-sig")),
                            args.output, args.existing_ips, backend, recovery)
            print(f"{len(report['changed_events'])} changed; IPS SHA-256 {report['ips_sha256']}")
    except (ValueError, OSError, ImportError, KeyError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
