# 1.1 development research and validation

Date: 2026-10-04 (Asia/Shanghai). Development branch `version/1.1`, based on
stable `v1.0`, commit `b95229a`. This is an unpublished `1.1-dev` candidate.

## Source review

- [Toolkit](https://github.com/CyleAR/hololive-toolkit), inspected at commit
  `8089309806b10ce6cc0ae660a46d2217eb815a1e`: OCTO manifest decoding, asset
  downloading/deobfuscation and UnityPy export; not a real-time UI/state API.
- The installed game's OCTO index (revision 94) contains fishing artwork,
  but the core UI is in local Addressables bundles. A read-only scan of
  1,852 local bundles found `ParkFishingScreen`, fishing result dialogs,
  `ParkFishingPictureBookScreen`, login-bonus and birthday screens.
- Toolkit's extractor successfully exported 29 textures/sprites from
  `ParkFishingAtlas` with no extraction warnings. These include TAP, GET,
  fish, reel, gauge and book-paper artwork. Only a compact TAP letter mask
  is included in the assistant, with provenance and a rebuild tool.
- Native UI object names and layouts are research evidence, not a screenshot
  classifier. Extracted assets cannot prove that a modal is visible or that
  the game accepted input. Automatic fishing still uses screenshots/input.
- Reviewed [Issue #1](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/1),
  [#2](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/2),
  their comments, and new [#3](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues/3).
- Bilibili's [video](https://www.bilibili.com/video/BV1QTaH6fE6Z/) and API
  both returned HTTP 412; comments were not independently retrieved.
  The user supplied these reports: TAP not recognized; SetCursorPos fails;
  NEW not clicked while Continue/Start/TAP work; reeling stays at the bottom
  with the cursor pinned and no apparent pressing/manual intervention.

## Changes

- Ina reward strip: row-relative color consistency replaces the fixed bright
  cyan requirement. GET remains mandatory, with modal-close priority.
- Dark themed Continue and X candidates use local color tolerance. Continue
  still requires four white borders and glyphs; the X still requires a round
  ring/diagonals and confirmed modal paper. The beta's two-page/header guard
  prevents snowy preparation screens from being treated as an encyclopedia.
- TAP keeps its original circle/exclamation/text check and adds a letter-shape
  fallback using extracted shared-language artwork, blue outline and a separate
  exclamation below. It does not require locating a click target.
- TAP and reeling reuse any cursor point inside the captured client, with a
  center fallback for a cursor outside it. Reeling's fixed bottom coordinate
  is removed. Existing foreground, geometry, occlusion and release checks remain.
  SetCursorPos is skipped when the cursor is already at the chosen point.
- JPEG encoding, annotation and image writes use a worker with at most three
  pending frames. Old pending evidence is discarded; latest frames coalesce.
  Images are at most 1280px wide and 192 KiB each. Retain 64 event images plus
  latest, and two 4 MiB trace segments. Normal diagnostics are bounded to
  approximately 21 MiB per session ZIP; optional video is explicitly excluded.
- On stop, release mouse input first, drain the bounded worker, then create
  `diagnostics.zip`. Writer failures are reported; a stalled worker gets a
  five-second close timeout and no misleading complete archive.
- Trace appends background write latency, discarded-frame count, input-down
  and move-call counters. Runtime exceptions retain their frame and reason.
  Counters describe Windows API calls, not game acceptance.

## Evidence and limits

- Ina public screenshot: `reward_continue` at widths 960, 1280, 1663, 1920,
  2560. The original 1.0/beta baseline was `unknown`.
- Issue #2 manual video: all 799 frames replayed. TAP remains 24 frames,
  11.600–12.483s; one BiteGuard decision at 11.667s. Main reel HUD 325 frames,
  323 complete marker pairs, 324 tracker results; unchanged from baseline.
  This is offline recognition and hypothetical control, not actual fishing.
- Ina size sample: original PNG 896,988 bytes; JPEG 64,066 bytes at 1280×720,
  quality 82; still returns `reward_continue`. Two-image sample ZIP 117,402
  bytes. JPEG encoding measured 13.16ms on this machine, in the worker.
- Synthetic 4K noise respects the image-byte limit; deterministic slow-encoder,
  bounded queue, retention, archive exclusions, writer error and CSV rotation
  tests cover diagnostics under load/failure.
- All 163 unit tests passed, including UI layout, localization, input safety,
  palette/shape positives and negatives, and bounded asynchronous diagnostics.
- Replayed 159 historical screenshots from nine available diagnostic folders;
  scene/TAP/catch classifications match stable 1.0 on all of these. Candidate
  classification stayed unchanged after the character-palette changes. These cover TAP/reel,
  result, material overlay, encyclopedia and item detail. They do not include
  every user's reported failing frame. No private diagnostic screenshots are
  added to Git or release packages.
- Extended actual-palette checks: 62 published Character master entries,
  all five RGB fields cross-checked against JP, and local CharacterColorSetter
  references inspected. The inferred control field (color4) passes 6,696
  offline cases covering six fixture layouts, six language settings and nine
  scenes. Neutral/dark X, grey rewards and small-button antialiasing were fixed.
  Full field provenance, inference limits and per-character results are in
  [CHARACTER-PALETTES-1.1.md](CHARACTER-PALETTES-1.1.md). These are recoloured
  geometry fixtures, not 62 live game screenshots or multilingual glyph captures.

## Remaining verification and excluded scope

- TAP/NEW complaints without corresponding failure frames cannot be declared
  exhaustively fixed by the new fallback or palette tests.
- The user explicitly excluded SetCursorPos investigation from 1.1 and reports
  that administrator mode solves it on their machine. No automatic elevation
  or permission changes are implemented. Navigation still needs movement.
- A bottom-stuck reel can involve missed markers, latency or rejected input.
  No reeling physics/controller constants were retuned from incomplete reports.
  Diagnose with the compact ZIP and the newly added input/timing fields.
- The user explicitly excluded day-change/login-bonus return from 1.1.
  Automatic bait switching was removed at the user’s request.
- No new live fishing success claim: the game's window was no longer available
  when live verification was attempted. Release and issue status are unchanged.

## ZIP-only diagnostics with dated names

Per user request, successful shutdown now retains only the verified diagnostic
ZIP, removing its byte-identical JPEG, trace and manifest originals. Session
folders use `YYYY-MM-DD_HH-MM-SS` plus a collision suffix; ZIP files use
`diagnostics-YYYY-MM-DD_HH-MM-SS.zip`, with the shutdown timestamp. Extracting
by ZIP filename therefore also produces a dated folder. The GUI help in all
six languages describes ZIP-only retention and preserving originals on failure.

The archive is written to a temporary file and CRC-validated before atomic
publication. Original contents are also compared before any cleanup; changed
originals prevent cleanup. Optional video and unrelated files are not packaged
or deleted. Failed encoding/packing retains available originals. Repeated
close returns the same complete ZIP without overwriting it with an empty one.
Input remains released before archiving and cleanup.

The four supplied completed sessions with existing ZIPs were checked and
188 byte-identical originals removed, preserving their archives. Older
unarchived folders were not deleted. Tests cover ZIP-only retention, dated
names, unrelated/video preservation, write failures, changed-original safety,
repeated close and runtime shutdown ordering.

## Developer-help wording revision

Per the supplied screenshot, the two appended paragraphs about JPEG retention,
ZIP filename format and cleanup are removed from the help dialog. The first
paragraph now introduces diagnostics under date-and-time titles, preserving the
purpose and no-upload sentence. All six help translations were updated. The
nine localization/layout tests passed; diagnostic saving behavior is unchanged.


## Independent Windows global start (start-r2)

The follow-up still failed in game: Stop worked while Start only showed a
connecting state after switching to the assistant. The previous activation
change did not establish or repair the underlying cause. Start was sampled
by Tk after callbacks; Stop was sampled by the fishing worker. Replace the
start path with RegisterHotKey on a dedicated thread and a windowless Windows
message queue, using MOD_NOREPEAT. Rebinding unregisters the old hotkey, uses
a fresh identity, and suppresses an already-held key until release. Capture
and modal dialogs suspend registration; unavailable keys are reported.

Only the GUI reads Tk settings, publishing an immutable snapshot. The listener
launches the fishing worker directly from that snapshot and queues UI updates;
it never calls Tk. A launch lock prevents duplicates, and run IDs discard old
progress/done messages after a new run. The normal Start button uses the same
launch path. Window lookup now uses correctly typed ctypes calls, releasing
the GIL during native operations, and prefers the already-foreground game.

The footer identifies start-r2. GUI logs show registered key, start source,
and three initialization stages. A bounded 128 KiB startup.log plus one
backup under LocalAppData/HololiveFishingAuto records these stages even when
developer screenshots are off. It is local and is never uploaded.

147 tests pass. Integration registers unusual Ctrl+Alt+Shift+F21/F22/F23 test
combinations and posts WM_HOTKEY only to our own listener thread; no hardware
key events or game input are sent. It proves launching and restarting without
processing Tk events, duplicate prevention, old-run filtering, registration
conflicts, rebinding and cleanup. Six language / four DPI layout checks pass.
This does not prove the reported user's game has been fixed; a new live run
with start-r2 is still needed.

References: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey
and https://learn.microsoft.com/en-us/windows/win32/inputdev/wm-hotkey .
