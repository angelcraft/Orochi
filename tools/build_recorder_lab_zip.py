#!/usr/bin/env python3
"""Create a reversible, *unvalidated* Atmosphère lab ZIP locally.

This is deliberately NOT run by GitHub Actions: it requires an original
main.npdm extracted by the owner and never publishes copyrighted metadata.
It does not touch the SD card.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

try:
    from tools.npdm_one_svc import ORIGINAL_NPDM_SHA256, PROGRAM_ID, NpdmError, patch
except ModuleNotFoundError:  # python tools/build_recorder_lab_zip.py
    from npdm_one_svc import ORIGINAL_NPDM_SHA256, PROGRAM_ID, NpdmError, patch

CONTENTS = f"atmosphere/contents/{PROGRAM_ID:016X}/exefs"
BUILD_ID = "03ff4a3bec96bde3a2e37ce3aa4caa0cae8935a8000000000000000000000000"
ORIGINAL_MAIN_SHA256 = "494c35e74dae893615980134f8be7673779f8d4b9eb9601e0f1b130d5ee1870e"
PLUS240_SHA256 = "e4da82980508cebdfda5e003d829675a4997ecef7999950642779ab53016781c"
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


def create_bundle(npdm: bytes, module: bytes, *, sd_access: bool = False) -> tuple[dict[str, bytes], dict]:
    if module[:4] != b"NSO0" or len(module) < 0x1000:
        raise NpdmError("Not a plausible AArch64 subsdk1 NSO")
    npdm_out, report = patch(npdm, sd_access=sd_access)
    files = {
        f"{CONTENTS}/subsdk1": module,
        f"{CONTENTS}/main.npdm": npdm_out,
        "GROOVE_RECORDER_LAB_README.txt": NOTES.encode("utf-8"),
        "npdm-preflight.json": (json.dumps(report, indent=2) + "\n").encode("utf-8"),
    }
    return files, report


def check_originals(main: Path, npdm: bytes) -> None:
    image = main.read_bytes()
    if image[:4] != b"NSO0" or image[0x40:0x60].hex() != BUILD_ID:
        raise NpdmError("Build ID de main distinto del Groove 1.0.0 verificado")
    if hashlib.sha256(image).hexdigest() != ORIGINAL_MAIN_SHA256:
        raise NpdmError("El SHA-256 de main no coincide con el original verificado")
    if hashlib.sha256(npdm).hexdigest() != ORIGINAL_NPDM_SHA256:
        raise NpdmError("El SHA-256 de main.npdm no coincide con el original verificado")


def check_sd(sd_root: Path, module_ids: set[str] | None = None) -> list[str]:
    atmosphere = sd_root / "atmosphere"
    if not atmosphere.is_dir():
        raise NpdmError("Indica la raíz de la SD que contiene la carpeta atmosphere")
    exefs = sd_root / CONTENTS
    if exefs.exists() and not exefs.is_dir():
        raise NpdmError(f"Ruta ExeFS en conflicto: {exefs}")
    conflicts = [p for p in (exefs.parent / "exefs.nsp", exefs.parent / "exefs.stub",
                            *(exefs / name for name in ("main", "main.stub", "rtld",
                              "rtld.stub", "sdk", "sdk.stub", "main.npdm", "main.npdm.stub")),
                            *(exefs.glob("subsdk*")))
                 if p.exists() or p.is_symlink()]
    if conflicts:
        raise NpdmError("Overrides existentes (se conservan): " +
                        ", ".join(str(p.relative_to(sd_root)) for p in conflicts))

    target_ids = {BUILD_ID} | (module_ids or set())
    known_patches = []
    for patch_file in (atmosphere / "exefs_patches").glob("*/*"):
        stem = patch_file.stem.lower()
        # Atmosphère accepts shortened names when the missing bytes are zero.
        if patch_file.suffix.lower() != ".ips" or len(stem) % 2 or len(stem) > 64:
            continue
        module_id = stem.ljust(64, "0")
        if module_id not in target_ids:
            continue
        if (module_id != BUILD_ID or
                hashlib.sha256(patch_file.read_bytes()).hexdigest() != PLUS240_SHA256):
            raise NpdmError(f"IPS para este Build ID sin verificar: {patch_file}")
        known_patches.append(patch_file.relative_to(sd_root).as_posix())
    if len(known_patches) > 1:
        raise NpdmError("Se detectaron varias copias del IPS +240 para el mismo Build ID")
    return known_patches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_npdm", type=Path)
    parser.add_argument("subsdk1", type=Path)
    parser.add_argument("output_zip", type=Path)
    parser.add_argument("--lab-ack", action="store_true",
                        help="Acknowledge the NPDM+hook candidate is NOT validated on hardware")
    parser.add_argument("--sd-root", type=Path, required=True,
                        help="SD mount for read-only conflict checks (never modifies SD)")
    parser.add_argument("--original-main", type=Path,
                        help="Original main NSO (default: main beside original_npdm)")
    args = parser.parse_args()
    if not args.lab_ack:
        parser.error("Explicit --lab-ack required; this package is unvalidated")
    if args.output_zip.exists():
        parser.error("Refusing to overwrite an existing output ZIP")
    if args.output_zip.resolve().is_relative_to(args.sd_root.resolve()):
        parser.error("La salida debe quedar en el PC, fuera de la SD indicada")
    try:
        main = args.original_main or args.original_npdm.with_name("main")
        original = args.original_npdm.read_bytes()
        check_originals(main, original)
        if any(main.parent.glob("subsdk*")):
            raise NpdmError("El ExeFS de origen ya contiene subsdk")
        module = args.subsdk1.read_bytes()
        files, report = create_bundle(original, module, sd_access=True)
        module_ids = {module[0x40:0x60].hex()}
        for name in ("rtld", "sdk"):
            sibling = main.with_name(name)
            if sibling.is_file():
                with sibling.open("rb") as stream:
                    header = stream.read(0x60)
                if header[:4] == b"NSO0":
                    module_ids.add(header[0x40:0x60].hex())
        patches = check_sd(args.sd_root, module_ids)
    except (NpdmError, OSError) as exc:
        parser.error(str(exc))
    files["npdm-preflight.json"] = (json.dumps({
        **report, "target_build_id": BUILD_ID, "known_ips": patches,
        "override_sha256": {name: hashlib.sha256(data).hexdigest()
                            for name, data in files.items() if name.startswith(CONTENTS)},
    }, indent=2) + "\n").encode("utf-8")
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
