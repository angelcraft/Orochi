# Mobile handoff — Groove Switch / Remix 1 (2026-11-07)

This document preserves a verified handoff for continuing development when the original Windows PC is unavailable. **It is not a backup of local-only source files.** Do not claim that a local commit, archive, game dump, or edited asset is stored on GitHub unless its presence has been verified.

## Verified remote status

- Repo: `angelcraft/Orochi`
- Branch: `experiment/groove-recorder-all-games`
- Verified remote head: `d703fd1f372cbbaf63ef3a8eba0c3e8f4085e8e0`.
- Available remotely: `tools/remix1_sequence.py`, `RECORDER_REMIX1_SEQUENCE.md`, `tests/test_remix1_sequence.py`. This bridge can snapshot Remix 1 native data and export restricted reversible timing IPS changes.
- Existing confirmed capability: 40 native actions, 767 waits, 23 observed scene transitions plus initial scene; 18 isolated retiming windows verified by existing backend. It cannot yet insert arbitrarily new events or reorder scene control.
- Prior Switch-tested operation: moving the third Remix 1 ring cue from beat 74 to 75; the bridge reproduced the prior IPS byte-for-byte. New changes and omission patch have not been hardware-tested in this handoff.
- `angelcraft/RhythmParadiseAfterGroove` is a **private** remote repo. Branch `work/headless-host` exists, but Bionic's latest local Android touch changes have not been verified pushed.
- `angelcraft/HeavenStudio2` is a **private** remote repo, but local commit `7d57938` (Groove cycle view) was not on branch `experiment/groove-hoop-trundling` at the time of this note.

## Important PC-only assets at risk (not remotely verified)

1. Local Switch Studio commit `f2d8bb0` on branch `research/native-cue-recovery`: mapping audit for the user's visually edited `1.rhref` and export of third ring beat 74→75. Check the local repo remotes and push the branch to a suitable **private** GitHub repo. The related earlier local commit is `e4922de`.
2. Music/tempo conversion module in local directory `work/groove-remix1-music`. The report describes CWVTool WAV→CWV encoding, WMB timing validation, and RomFS-only packaging; full encoding with a supplied WAV was not run.
3. RHREfresh Switch Edition Java editor/source and Windows builds in workspace `outputs/RHREfresh-Switch-Edition-Windows.zip`, `outputs/Hoop-Trundling-native-edit`, etc. Back up sources and binaries.
4. Human edited `1.rhref` and `Remix-1-Switch-Intento.rhref`, native-reference RHREs, `remix1-native-sequence.json`, audit JSONs, ring-patch ZIPs, and any original-game files required for rebuilding. These were available as uploaded artifacts in prior ChatGPT conversations; they were not checked into GitHub.
5. Any uncommitted Bionic edits to AfterGroove and local Heaven Studio work.

## Backup priorities before the PC is lost

1. Make one **private** compressed backup of the entire original Codex workspace (including `work` and `outputs`) and upload it to an account-controlled cloud drive. Verify the uploaded file can be listed and downloaded. Never publish proprietary ROM/NSO, music, private credentials, `.env`, tokens, or personal documents to a public repository.
2. In each Git checkout: `git status -sb`, `git log -1 --oneline`, `git remote -v`, then commit/push to the correct remote. Do not assume `origin` means github.com: some local clones were configured to push to another local Windows checkout.
3. Keep a second independent backup, if possible.
4. Check hashes and completeness; recover original filenames. Never run force pushes, hard resets, or destructive GC when repos may have missing objects.

## Mobile continuation

- Read/edit published source in the browser: `https://github.dev/angelcraft/Orochi`.
- Use GitHub Codespaces for terminal, Python/C++ builds, and tests; use GitHub Actions for CI/artifacts. Neither requires the original PC if the code and required non-public assets were backed up.
- RHREfresh graphical Java editor and direct Switch hardware validation are **not** available in a browser by default.
- Recommended next development: reuse the editor/IPS backend and verify the mapping from observed musical cue time to native call time for rings/flowers; proceed separately on CWV/WMB song replacement without inventing a complete remix export.
- Native format must distinguish command-call timing from visual/audio/input timing. Preserve hypotheses in metadata and do not shift all cue times using a single universal offset.

## Source notes

- `RECORDER_REMIX1_SEQUENCE.md` and `RECORDER_NATIVE_INPUTS.md` are authoritative technical documents for currently verified native coverage.
- The latest independent reports: local `f2d8bb0` (40 mappings, 17 tests) and local Groove music module (2 tests); these **reports alone** do not constitute a remote code backup.
