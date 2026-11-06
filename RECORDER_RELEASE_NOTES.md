# Groove Recorder — experimental multi-minigame capture

**Target:** Rhythm Heaven Groove 1.0.0 (Title ID `0100D9F01D474000`).

**State:** Development build for static and CI verification. Switch loading remains unverified. The original NPDM lacks `svcMapProcessMemory` (0x74) in both ACI0 and ACID, which LibHakkun uses for its writable code aliases. The one-SVC candidate changes the signed ACID payload. The LibHakkun reference also changes other permissions. Neither candidate is distributed here.

## Implemented observations

- Stage factory creations (last-created ID, *not necessarily active*)
- Sequence wait requests
- SceneRing hoop calls
- Shared scene SFX scheduling requests
- BGM / Wavmark requests
- Subscene initialization and cue-enable requests
- Thread append requests
- 84 cataloged actions across 32 scene classes, including the existing hoop observation through the same trampoline
- Typed scalar arguments, IEEE-754 float bits and pointer presence. Pointer contents and addresses are omitted.

The 93 distinct entry words were checked against the original 1.0.0 executable. Each hook checks its word at runtime and requires single-instruction branch reach in both directions. Gameplay callbacks use signatures from Orochi's scene declarations. Switch ABI behavior and coverage still require a gameplay trace. Expected inputs, controller input, judgement windows and outcomes remain unresolved.

## Logs

If/when runtime and NPDM compatibility are verified, the module attempts to append debug records to `sdmc:/Orochi/groove-recorder.log`. No arbitrary 32 MiB rotation/truncation is used. The buffer is finite and tracks lost events; storage exhaustion is still possible. File I/O is done in a periodic main-loop drain, not inside the game callbacks. Each run has a session ID.

To convert a collected log:

```sh
python tools/read_groove_recorder.py groove-recorder.log events.jsonl coverage.json
```

The reader supports legacy records and v3 actions. Keep the gameplay catalog beside the reader. The report separates installed gameplay-hook count from observed command IDs. Unknown beat and input fields are null.

## Known unresolved risks

1. Atmosphère NPDM loading and `svcMapProcessMemory` permission.
2. ABI and exact function offsets for newly instrumented common API entrypoints.
3. Buffer overflow and timing effects in dense remixes (counts lost events).
4. Actual identification of active scene, tempo clock, expected inputs and judgement callbacks.
5. Slot collision with the separate experimental aro-35 `subsdk1`; never install both together.

The mod **rusino - Looping the Rooms** on GameBanana, mod 701655, is a reference custom remix, but its downloadable contents have not yet been independently inspected. Do not assume its gameplay-cue layout from its title or screenshots.

Source branch `experiment/groove-recorder-all-games`.
