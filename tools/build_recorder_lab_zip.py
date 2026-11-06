#!/usr/bin/env python3
"""Create a reversible, *unvalidated* Atmosphère lab ZIP locally.

This is deliberately NOT run by GitHub Actions: it requires an original
main.npdm extracted by the owner and never publishes copyrighted metadata.
It does not touch the SD card.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from tools.npdm_one_svc import PROGRAM_ID, NpdmError, patch

CONTENTS = f"atmosphere/contents/{PROGRAM_ID:016X}/exefs"
NOTES = """Groove Recorder NPDM laboratory bundle (UNVALIDATED)

Only for testing with Groove 1.0.0 in a backed-up Atmosphère emuMMC.
This ZIP was assembled from the owner's original main.npdm; do not share it.
It has NOT been proven to load on a real Switch.
Do not merge with an existing subsdk1 or main.npdm override.

Caution: A modified ACID is no longer signed as the original. Although
Atmosphère may use the signature of the original metadata for an override,
acceptance is not guaranteed. A failure may crash the game on launch.

Reversion: restore any previous override(s), then remove both of these
experimental files from atmosphere/contents/TITLEID/exefs on the SD.
Do not modify sysMMC or a title's installed NCA.
The logger appends to sdmc:/Orochi/groove-recorder.log without an arbitrary
32 MiB limit; monitor free storage.
"""


def create_bundle(npdm: bytes, module: bytes) -> tuple[dict[str, bytes], dict]:
    if module[:4] != b"NSO0" or len(module) < 0x1000:
        raise NpdmError("Not a plausible AArch64 subsdk1 NSO")
    npdm_out, report = patch(npdm)
    files = {
        f"{CONTENTS}/subsdk1": module,
        f"{CONTENTS}/main.npdm": npdm_out,
        "GROOVE_RECORDER_LAB_README.txt": NOTES.encode("utf-8"),
        "npdm-preflight.json": (json.dumps(report, indent=2) + "\n").encode("utf-8"),
    }
    return files, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_npdm", type=Path)
    parser.add_argument("subsdk1", type=Path)
    parser.add_argument("output_zip", type=Path)
    parser.add_argument("--lab-ack", action="store_true",
                        help="Acknowledge the NPDM+hook candidate is NOT validated on hardware")
    parser.add_argument("--sd-root", type=Path,
                        help="Optional SD mount for read-only conflict checks (never modifies SD)")
    args = parser.parse_args()
    if not args.lab_ack:
        parser.error("Explicit --lab-ack required; this package is unvalidated")
    if args.output_zip.exists():
        parser.error("Refusing to overwrite an existing output ZIP")
    if args.sd_root is not None:
        if not args.sd_root.is_dir():
            parser.error("SD root not found")
        exefs = args.sd_root / CONTENTS
        conflicts = [p for p in ("main.npdm", "subsdk1")
                     if (exefs / p).exists()]
        if conflicts:
            parser.error("Existing override(s) found on SD: " + ", ".join(conflicts))
    files, report = create_bundle(
        args.original_npdm.read_bytes(), args.subsdk1.read_bytes()
    )
    with ZipFile(args.output_zip, "x", compression=ZIP_DEFLATED) as archive:
        for name, payload in sorted(files.items()):
            archive.writestr(name, payload)
    print(json.dumps({
        "status": "unvalidated laboratory ZIP; do not treat as safe install",
        "output": str(args.output_zip),
        "entries": sorted(files),
        "npdm_audit": report,
    }, indent=2))


if __name__ == "__main__":
    main()
