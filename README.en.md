# Hololive Dreams Auto Fishing

[Known issues and workarounds](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)

[繁體中文](README.md) · [简体中文](README.zh-CN.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

An auto-fishing assistant for the Windows version of **hololive Dreams**. It uses screen recognition and normal mouse input to handle bites, reeling, catch results, and the next round.

## Download

Open [GitHub Releases](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/latest) and download `Hololive-Dreams-Fishing-Auto-v1.1.1.exe` from the release assets.

Simply run this single EXE.

## Features

- Recognizes bite prompts, tracks the fish and catch zone, and controls reeling.
- Handles Continue / Next buttons on result screens and closes new encyclopedia entries and item pop-ups to resume fishing.
- Six languages: 繁體中文, 简体中文, English, 日本語, 한국어, and Indonesian. Selecting a language changes the assistant interface and messages.
- Displays the catch count for the current run. Set a target count to stop when it is reached.
- The Start shortcut defaults to F8 and Stop to F9. Click either setting field and press a new key or combination to customize it. The two shortcuts must not conflict.
- Activity log.
- Optional local developer diagnostics.

## Quick start

1. Open the game, prepare bait, and enter the fishing screen.
2. Run the EXE and select a language under “Language”.
3. Set a catch target; `0` means unlimited. To change the stop shortcut, click its field and press the desired key combination.
4. Click Start or press the Start shortcut. The assistant attempts to activate the game; keep the game in the foreground and fully visible while it runs.
5. Stop with the Stop shortcut, the Stop button, or by switching windows. Starting again resets the counter to zero and counts toward the catch target from the beginning.

## Requirements and limitations

Windows 10 / 11 x64 and the Windows game are required. Keep the game client area at 16:9; do not minimize, cover, or resize it during operation. Background fishing and resuming fishing after the daily reset at 5:00 AM JST are not supported. The assistant does not automatically purchase bait, change maps, or replenish game resources.

Character colors, animations, resolution, performance, and game updates may still affect recognition and input; stop and provide diagnostics if something goes wrong. This is an unofficial tool. It does not read or modify game process memory, saves, or game files. This tool is intended solely for learning Python programming and researching and exchanging knowledge about image recognition technology. Check the game's rules on automation yourself. Do not use this tool to disrupt the game's ecosystem or for any commercial or profit-making purposes. The developer accepts no responsibility for any problems resulting from its use.

## Reporting problems and Developer mode

Report continuation failures, tracking issues, or other problems through [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues).

Enable Developer mode before reproducing the issue. It saves state screenshots, catch cards, tracking data, and timing information locally; nothing is automatically uploaded. Screenshots include the game view, and diagnostics add performance overhead.

Click `?` beside Developer mode to view and open the diagnostic folder:

JPEG screenshots are saved in the background, up to 192 KiB each. The latest 64 event images and latest view are retained, along with two recent 4 MiB trace segments. The diagnostic ZIP excludes optional video.

```text
%LOCALAPPDATA%\HololiveFishingAuto\sessions\
```

The path follows your Windows account. Each run creates a timestamp-named folder. Include the app version, game language / character, resolution, Windows display scaling, a description, and the automatically generated `diagnostics-YYYY-MM-DD_HH-MM-SS.zip` after stopping. Review screenshots for information you do not want to share before submitting them.

## Source and license

See the [development guide](docs/DEVELOPMENT.md) for source setup, single-file builds, and offline tests. Code is [MIT licensed](LICENSE); rights to the fish character and game belong to their respective owners.
