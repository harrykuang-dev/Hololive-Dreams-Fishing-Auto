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
  Bait switching was subsequently authorized and is described below.
- No new live fishing success claim: the game's window was no longer available
  when live verification was attempted. Release and issue status are unchanged.

## Optional depleted-bait recovery

User-requested, default-off GUI checkbox and CLI `--auto-bait`. A confirmed
fish result plus red triangular warning latches recovery immediately. Dim
Continue glyphs trigger one settled probe click (a prior Continue click counts),
then hold navigation while waiting for warning evidence; two
unsuccessful Continue clicks trigger a quiet inspection and bounded stop.
A verified result, disabled Continue and Change Bait pill held for 1.5 seconds
also latch recovery even when no red warning is captured. Blinking or
temporarily absent warnings cannot reset the latch. The same
controller blocks generic dialog-X and TAP actions until recovery completes.

Recovery waits 0.65 seconds, detects the Change Bait pill, opens the dialog,
verifies the first dough icon and infinity quantity, selects that cell, then
requires 0.5 seconds of matching selection corners and dough preview before
confirming. Returning requires an enabled Continue and no warning for 0.65
seconds. Each stage has an 8-second timeout, at most three actions spaced
1.2 seconds apart. Uncertain frames cause a pause or stop rather than more
Continue clicks. One-shot mode does not switch bait. Catch-target completion
and existing stop/focus/input checks retain priority.

The user's manual video provides actual exhaustion, empty-current-bait,
selected-infinite-bait and returned-result frames. The extracted result prefab
has park-character tint on the Change Bait icon/text/outline. The selection
prefab uses separate tint setters; in the recording its header is blue while
the park theme is purple. Recognition ignores localized wording and does not
require either theme hue. Six assistant language settings and 62 published
main tints are checked offline; recolouring does not reproduce live character
screens or actual localized game glyphs. No recording is included in Git.

See `tests/test_bait.py` for blinking/absent warnings, zero vs infinity,
wrong selection, bounded retries, timeouts, tint fixtures and runtime priority.
No automated game input was sent during this verification. A manual recording
cannot validate the game's response to hypothetical clicks.

### Live diagnostic correction: missing warning before Continue

The supplied session `20261004-135949-109187900` reached `bait_inspect`
and timed out after 8 seconds. Three diagnostic result images show disabled
Continue and a valid Change Bait pill, but no red triangle. The user clarified
that clicking Continue triggers the warning. The original controller had
blocked Continue while requiring that warning, preventing its own evidence.

The corrected controller issues at most one Continue probe after 0.25 seconds
of inspection, then pauses. A Continue already issued by navigation counts
as the probe. The red-warning latch remains; persistent disabled-result
geometry now also allows recovery after 1.5 seconds. Replaying the actual
failed image at 10 Hz predicts one probe at 0.3 seconds and Change Bait at
1.9 seconds, with no repeated Continue clicks. This is offline verification,
not evidence that this corrected EXE has yet completed a live bait change.

### Live follow-up: confirmed recovery and premature Continue

Session `20261004-141007-081865100` confirms the grey-result fallback:
result 19.3331s, opening 21.7595s, selecting 22.1646s, selection click
22.9779s, confirmation click 24.1859s, returning 24.3406s, ordinary result
25.1190s, Continue 25.3676s, a new reel 35.6553s and the second catch
43.3405s. The Japanese dialog shows the formerly selected red sliced bait
at zero and the later selected first dough bait at infinity. This is evidence
of a completed bait change and subsequent fishing in this supplied session.

The premature click is also confirmed: the first result's Continue was
clicked at 19.5766s, only 0.2435s after card recognition, while the diagnostic
card image has no bottom buttons. The card's fallback coordinate had bypassed
actual button readiness. The second catch also received premature retries.

The enabled switch now holds all ordinary result navigation as `bait_settling`
until the card has been observed for at least 1.5s and the actual Continue
button plus Change Bait pill have been continuously detected for 0.65s.
An absent button is not established by a fallback coordinate. Red warnings
seen during settling are retained; absent result frames reset button stability.
Settling is bounded at 8s. The one-probe and persistent-grey fallback then run
as before. A simulated 10Hz timeline from this session's actual early card and
later ready-button images first probes at 2.0s and opens Change Bait at 3.6s,
instead of clicking at 0.24s. The updated timing itself is not yet live-tested.

### Live follow-up: restored scroll position clips the first bait

Session `20261004-142121-353276100` completed normal fishing for more than
six minutes, then entered inspect 367.4449s and opening 368.1060s. The change
click at 371.1208s opened the correct dialog. Both later diagnostic images show
a restored lower list position, selected fried chicken at zero, and the first
infinite dough bait partially clipped under the header. The fixed first-cell
coordinates and required full dough icon prevented recognizing the open dialog;
the controller timed out in opening. No selection or confirmation was issued.

Quantity pills are now searched throughout the first-column viewport. The
infinity marker must have white quantity surroundings and visible orange dough
art above it; the click point comes from that visible artwork. The selection
focus checks move with the infinity quantity; the bottom corners remain usable
when the header clips the top corners. A confirmed header, preview panel and
at least three quantity pills also establish a bait list when infinity is off
screen. In that case only a bounded upward wheel operation is allowed in the
list viewport, then the same infinity/selection proof is required. Scroll and
selection have separate three-attempt budgets, shared 1.2s spacing and the
existing 8s stage timeout. Wheel input retains client, occlusion and foreground
checks and is recorded as `scroll_up` in the trace.

Both actual failed dialog images now return dialog=True, selected=False and
a visible first-bait target around (315,183) in the saved 1280x720 image;
opening advances to selecting and requests that target. Synthetic tests cover
partially clipped selected bait, a completely hidden first cell, bounded
scrolling, selecting after the scroll budget and wheel focus/occlusion guards.
All 160 tests and the 2,232 actual-frame tint/size/language-setting cases pass.
No real game input was sent during this development; this correction still
requires a new live check.

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
