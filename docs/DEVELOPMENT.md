# 開發說明 / Development guide

[繁體中文](../README.md) · [简体中文](../README.zh-CN.md) · [English](../README.en.md) · [日本語](../README.ja.md) · [한국어](../README.ko.md) · [Indonesian](../README.id.md)

## 環境 / Environment

Windows 10 / 11 x64. The current release is built with Python 3.13 x64.
Runtime and build dependencies are declared in `requirements.txt` and `requirements-build.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe .\gui.py
```

The GUI uses automatic screen recognition and does not require a legacy profile.
Do not change reeling parameters solely on the basis of synthetic simulations.

## 單檔建置 / Single-file build

With the build environment active:

```powershell
.\.venv\Scripts\Activate.ps1
.\build.ps1
```

Output: `dist\Hololive-Dreams-Fishing-Auto-v1.1.1.exe`.
The EXE includes its runtime, icon assets and high-DPI manifest; users need only the EXE.

If an older EXE is running, close it or choose a different output folder before building.
Do not overwrite or terminate a running user's copy without checking.

## 驗證 / Validation

Run on Windows; GUI tests create temporary Tk windows but do not start fishing.

```powershell
python -m unittest discover -s tests -v
python -m fishing_auto --help
python tools/control_benchmark.py
python tools/verify_icon.py dist/Hololive-Dreams-Fishing-Auto-v1.1.1.exe
Get-FileHash dist/Hololive-Dreams-Fishing-Auto-v1.1.1.exe -Algorithm SHA256
```

Tests cover recognition, input safety, continuation, counters, shortcuts, translations,
layout scaling and icon packaging. Offline tests and synthetic benchmarks are not
proof of in-game success rates.

## 圖標 / Icon

The active asset is `assets/fish-clear.ico`; both the EXE and Tk windows must use it.
Artwork and generation provenance are documented in [ICON.md](../assets/ICON.md).

```powershell
python tools/make_icon.py assets/fish-clear.png assets/fish-clear.ico --pixel
python tools/preview_icon.py
```

The preview is a diagnostic contact sheet, not a source asset.

## 離線回放 / Offline replay

```powershell
python tools/replay_recording.py "local-recording.mp4" sessions/replay --hz 10
```

Replay analyzes local videos without sending game input. For timestamped traces,
preserve the original capture timestamps rather than inferring latency from nominal video FPS.

## 隱私 / Privacy

Never commit recordings, screenshots, session diagnostics, local calibration profiles,
account information or credentials. These local outputs are excluded by `.gitignore`.
The release asset must not contain user diagnostics.

## 研究工具 / Research tools

The `fishing_auto` package also contains legacy capture, manual calibration and replay
commands. Use `python -m fishing_auto --help` for their CLI entry point. They are not
required for the GUI and should not be confused with the single-EXE user workflow.
Historical verification notes remain under `docs/`; the README introduces the application.

## 1.1

Based on stable tag `v1.0` (`b95229a`); includes the beta preparation-screen guard.
See [1.1 research and validation](RESEARCH-1.1.md). The formal release is tagged `v1.1`.


Successful diagnostic shutdown leaves a dated ZIP only. Session folders use
`YYYY-MM-DD_HH-MM-SS` and ZIP filenames include shutdown time. Packed originals
are removed only after archive verification; packing failures retain originals.
Explicit recordings and unrelated files remain separate.

For every release, keep one standalone known-issues link immediately below the README title in all six languages, pointing to main/docs/KNOWN_ISSUES.md.

Normal mode writes no persistent startup journal. Developer mode includes a bounded
startup.log inside the dated diagnostic ZIP; verified packed originals are removed.
The earlier development build's two application-level startup journals are removed
on launch. Diagnostic ZIPs remain available for users to report problems.

Release `v1.1.1` fixes a smooth
water strip that suppressed TAP recognition. Stable releases remain linked from
the user guides. Private failure screenshots are replayed locally and are not
included in the repository or release assets.
