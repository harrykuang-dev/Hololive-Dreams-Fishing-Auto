# Hololive Dreams Auto Fishing

[Known issues and workarounds](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)

[繁體中文](README.md) · [简体中文](README.zh-CN.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

An auto-fishing assistant for the Windows version of **hololive Dreams**. It uses screen recognition and normal mouse input to handle bites, reeling, catch results, and the next round, with a simple graphical interface and no manual calibration required.

## Download

Open [GitHub Releases](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/latest) and download `Hololive-Dreams-Fishing-Auto-v1.0.exe` from the release assets.

The single EXE includes its runtime and icon assets. You do not need Python or additional files. A SHA-256 checksum file is also available; the source-code ZIP is not the runnable application.

## Features

- Recognizes bite prompts and tracks the fish and catch zone while reeling.
- Handles Continue / Next buttons and collection or item pop-ups to resume fishing.
- Six interface languages: 繁體中文, 简体中文, English, 日本語, 한국어, and Indonesian. This setting changes the assistant, not the game.
- Confirmed-catch counter and an optional catch target that stops the assistant.
- Every Start resets the counter to zero. Materials and unconfirmed results are not counted; counts are not saved.
- Customizable stop shortcut, F9 by default. Click the shortcut field and press a key or combination; refocusing the window does not rebind it.
- Simple light interface, high-DPI scaling, activity log, and optional local developer diagnostics.

## Quick start

1. Open the game, prepare bait, and enter the fishing screen.
2. Run the EXE and select the same language as your game.
3. Set a catch target; `0` means unlimited. To change the stop shortcut, click its field and press the desired key combination.
4. Click Start. The assistant attempts to activate the game; keep the game in the foreground and fully visible while it runs.
5. Stop with your shortcut, the Stop button, or by switching windows. Starting again resets the counter and starts a fresh target.

## Requirements and limitations

Windows 10 / 11 x64 and the Windows game are required. Keep the game client area at 16:9; do not minimize, cover, or resize it during operation. Background fishing, bait purchases, map changes, and resource replenishment are not supported.

Character colors, animations, resolution, performance, and game updates may still affect recognition and input; stop and provide diagnostics if something goes wrong. This is an unofficial tool. It does not read or modify game process memory, saves, or game files. This tool is intended solely for learning Python programming and researching and exchanging knowledge about image recognition technology. Check the game's rules on automation yourself. Do not use this tool to disrupt the game's ecosystem or for any commercial or profit-making purposes. The developer accepts no responsibility for any problems resulting from its use.

## Reporting problems and Developer mode

Report continuation failures, tracking issues, or other problems through [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues).

Enable Developer mode before reproducing the issue. It saves state screenshots, catch cards, tracking data, and timing information locally; nothing is automatically uploaded. Screenshots include the game view, and diagnostics add performance overhead.

Click `?` beside Developer mode to view and open the diagnostic folder:

```text
%LOCALAPPDATA%\HololiveFishingAuto\sessions\
```

The path follows your Windows account. Each run creates a timestamp-named folder. Include the app version, game language / character, resolution, Windows display scaling, a description, and a ZIP of the entire relevant session folder. Review screenshots for information you do not want to share before submitting them.

## Source and license

See the [development guide](docs/DEVELOPMENT.md) for source setup, single-file builds, and offline tests. Code is [MIT licensed](LICENSE); rights to the fish character and game belong to their respective owners.
