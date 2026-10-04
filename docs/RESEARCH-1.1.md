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
- All 132 unit tests passed, including UI layout, localization, input safety,
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
  Automatic bait switching is also outside this version's requested scope.
- No new live fishing success claim: the game's window was no longer available
  when live verification was attempted. Release and issue status are unchanged.
