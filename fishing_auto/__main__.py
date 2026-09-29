from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sys
import time

from .control import Controller
from .engine import Engine
from .profile import Profile
from .vision import Vision, read_image, save_image


def bounded_int(value):
    number = int(value)
    if not 1 <= number <= 100:
        raise argparse.ArgumentTypeError("rounds must be between 1 and 100")
    return number


def controller_for(profile):
    return Controller(direction=profile.direction, **profile.control)


def check_cycle(profile, auto_cycle):
    if auto_cycle:
        if not {"ready", "waiting", "bite"} <= profile.scenes.keys():
            raise ValueError("Auto-cycle needs calibrated ready/waiting/bite scenes")
        for name in ("ready", "bite", "success", "failure"):
            if "click" not in profile.scenes[name]:
                raise ValueError(f"Auto-cycle needs a calibrated {name} click")


def run(args):
    # Validate profiles before importing/constructing any Windows input object.
    profile = Profile.load(args.profile)
    vision = Vision(profile)
    check_cycle(profile, args.auto_cycle)
    from .windows import GameWindow, VideoRecorder
    path = Path(args.sessions) / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path.mkdir(parents=True, exist_ok=False)
    engine = Engine(controller_for(profile), args.rounds, args.auto_cycle)
    recorder = game = None
    reason = "not_started"
    started = time.perf_counter()
    frames = 0
    active_started = None
    metadata = {"mode": "observe_only" if args.observe_only else "live",
                "profile": str(Path(args.profile).resolve()), "rounds": args.rounds,
                "auto_cycle": args.auto_cycle, "nominal_recording_fps": args.fps,
                "live_success_claim": False}
    print("Click the game window within 5 seconds. Keep it visible. F9 stops and releases the reel.", flush=True)
    time.sleep(5)
    try:
        game = GameWindow()
        with (path / "frames.jsonl").open("w", encoding="utf-8") as log:
            while time.perf_counter() - started < args.seconds:
                loop_started = time.perf_counter()
                frame = game.capture()
                captured = time.perf_counter()
                if active_started is None:
                    active_started = captured
                if args.record and recorder is None:
                    recorder = VideoRecorder(path / "game.mp4", (frame.shape[1], frame.shape[0]), args.fps)
                observation = vision.observe(frame)
                decision = engine.step(captured, observation)
                if time.perf_counter() - captured > .10 or captured - loop_started > .15:
                    raise RuntimeError("Capture/analysis latency exceeds the safe control budget")
                if not args.observe_only:
                    game.hold(decision.hold, profile.reel_point)
                    if decision.click and not decision.stop:
                        game.click(profile.scenes[decision.click]["click"])
                if recorder:
                    recorder.write(frame)
                entry = {"frame": frames, "t": captured - active_started,
                         "observation": asdict(observation), "decision": asdict(decision),
                         "input_enabled": not args.observe_only,
                         "loop_ms": (time.perf_counter() - loop_started) * 1000}
                log.write(json.dumps(entry, allow_nan=False) + "\n")
                log.flush()
                frames += 1
                if decision.event:
                    print(f"{decision.event}: {engine.summary()}", flush=True)
                if decision.stop:
                    reason = decision.stop
                    save_image(path / "last.png", frame)
                    break
                time.sleep(max(0., 1 / args.fps - (time.perf_counter() - loop_started)))
            else:
                reason = "session_timeout"
    except (Exception, KeyboardInterrupt) as error:
        reason = f"{type(error).__name__}: {error}"
        print(reason, file=sys.stderr)
    finally:
        # Stop input first, regardless of recording/logging errors.
        try:
            if game:
                game.close()
        finally:
            try:
                if recorder:
                    recorder.close()
            finally:
                elapsed = time.perf_counter() - active_started if active_started is not None else 0.
                summary = {**metadata, **engine.summary(), "stop_reason": reason, "frames": frames,
                           "actual_capture_fps": frames / elapsed if elapsed else None,
                           "recording_frames": recorder.frames if recorder else 0,
                           "elapsed_seconds": elapsed,
                           "note": "Observe-only outcomes are observed gameplay, not bot successes. "
                                   "Template-confirmed live outcomes still need video review."}
                (path / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(summary, indent=2))
                print(f"Session: {path.resolve()}")
    return 0 if reason == "rounds_complete" else 2


def replay(args):
    """Recompute vision/decisions from local footage, without Windows input."""
    import cv2
    profile = Profile.load(args.profile)
    vision = Vision(profile)
    check_cycle(profile, args.auto_cycle)
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise ValueError("Cannot open replay video")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps < 6 or fps > 240:
        cap.release()
        raise ValueError("Replay needs a valid frame rate >= 6 FPS")
    timestamps = None
    if args.timestamps:
        with Path(args.timestamps).open(encoding="utf-8") as source:
            entries = [json.loads(line) for line in source if line.strip()]
        if any(entry["frame"] != i for i, entry in enumerate(entries)):
            cap.release()
            raise ValueError("Timestamp frame indexes must be contiguous")
        timestamps = [entry["t"] for entry in entries]
    engine = Engine(controller_for(profile), args.rounds, args.auto_cycle)
    count = 0
    reasons = []
    try:
        with Path(args.output).open("x", encoding="utf-8") as output:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if timestamps is not None and count >= len(timestamps):
                    raise ValueError("Video has more frames than timestamp log")
                t = timestamps[count] if timestamps is not None else count / fps
                observation = vision.observe(frame)
                decision = engine.step(t, observation)
                output.write(json.dumps({"frame": count, "t": t, "observation": asdict(observation),
                                         "decision": asdict(decision), "mode": "offline_replay"}) + "\n")
                if decision.stop and not reasons:
                    reasons.append(decision.stop)
                count += 1
        if timestamps is not None and count != len(timestamps):
            raise ValueError("Timestamp log has more frames than video")
    finally:
        cap.release()
    print(json.dumps({"mode": "offline_replay", "frames": count, "stop": reasons,
                      **engine.summary(), "live_success_claim": False}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Hololive Fishing Auto - calibrated development build")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="User-run game-client PNG capture, no input")
    capture.add_argument("output")
    calibration = commands.add_parser("calibrate", help="Human wizard using local game-client PNGs")
    for name in ("playing", "success", "failure"):
        calibration.add_argument(f"--{name}", required=True)
    for name in ("ready", "waiting", "bite"):
        calibration.add_argument(f"--{name}")
    calibration.add_argument("--axis", choices=("x", "y"), required=True)
    calibration.add_argument("--direction", type=int, choices=(-1, 1), required=True)
    calibration.add_argument("--output", default="profiles/local")
    calibration.add_argument("--auto-cycle", action="store_true")
    live = commands.add_parser("run")
    live.add_argument("--profile", required=True)
    live.add_argument("--rounds", type=bounded_int, default=1)
    live.add_argument("--auto-cycle", action="store_true")
    live.add_argument("--observe-only", action="store_true")
    live.add_argument("--record", action="store_true")
    live.add_argument("--fps", type=int, choices=(30, 60), default=60)
    live.add_argument("--seconds", type=int, choices=range(10, 601), default=180,
                      metavar="10..600")
    live.add_argument("--sessions", default="sessions")
    offline = commands.add_parser("replay")
    offline.add_argument("--profile", required=True)
    offline.add_argument("--video", required=True)
    offline.add_argument("--timestamps", help="Optional captured frames.jsonl for real frame intervals")
    offline.add_argument("--output", required=True)
    offline.add_argument("--rounds", type=bounded_int, default=1)
    offline.add_argument("--auto-cycle", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "calibrate":
            from .calibrate import calibrate
            calibrate(args)
        elif args.command == "capture":
            if Path(args.output).exists():
                raise ValueError("Capture output already exists")
            from .windows import GameWindow
            print("Click the game within 5 seconds; this command only captures its client.", flush=True)
            time.sleep(5)
            game = GameWindow()
            try:
                save_image(args.output, game.capture())
            finally:
                game.close()
        elif args.command == "replay":
            replay(args)
        else:
            return run(args)
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
