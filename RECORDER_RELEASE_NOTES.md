# Groove Recorder — experimental multi-minigame capture

**Target:** Rhythm Heaven Groove 1.0.0 (Title ID `0100D9F01D474000`).

**State:** Built for AArch64 / NSO as `subsdk1`, automated CI tests pass. This is **not an installable or validated Switch release**: `svcMapProcessMemory` may be missing from the original NPDM's capabilities, and loading a patched NPDM has not been verified on hardware. Do not install the module until that is resolved and its hooks are checked.

## Implemented observations

- Stage factory creations (last-created ID, *not necessarily active*)
- Sequence wait requests
- SceneRing hoop calls
- Shared scene SFX scheduling requests
- BGM / Wavmark requests
- Subscene initialization and cue-enable requests
- Thread append requests

These hooks have been checked by static reasoning and CI compilation, **not by a gameplay trace on Switch**. They will not necessarily capture every title/minigame, and **do not yet capture expected player inputs, actual controller input, judgement windows, or hit/miss outcomes**.

## Logs

If/when runtime and NPDM compatibility are verified, the module attempts to append debug records to `sdmc:/Orochi/groove-recorder.log`. No arbitrary 32 MiB rotation/truncation is used. The buffer is finite and tracks lost events; storage exhaustion is still possible. File I/O is done in a periodic main-loop drain, not inside the game callbacks. Each run has a session ID.

To convert a collected log:

```sh
python tools/read_groove_recorder.py groove-recorder.log events.jsonl coverage.json
```

The reader understands legacy `GROOVE_REC` and expanded `GROOVE_REC2`, and labels unknown musical beat and input data as null instead of inventing them.

## Known unresolved risks

1. Atmosphère NPDM loading and `svcMapProcessMemory` permission.
2. ABI and exact function offsets for newly instrumented common API entrypoints.
3. Buffer overflow and timing effects in dense remixes (counts lost events).
4. Actual identification of active scene, tempo clock, expected inputs and judgement callbacks.
5. Slot collision with the separate experimental aro-35 `subsdk1`; never install both together.

The mod **rusino - Looping the Rooms** on GameBanana, mod 701655, is a reference custom remix, but its downloadable contents have not yet been independently inspected. Do not assume its gameplay-cue layout from its title or screenshots.

Source branch: `experiment/groove-recorder-universal`. Keep previous functional RHRE/IPS builds untouched.
