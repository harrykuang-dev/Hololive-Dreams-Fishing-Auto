"""Offline runtime tests. All window input/capture is mocked."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fishing_auto.__main__ import run, replay
from fishing_auto.windows import GameWindow
import test_vision


class RuntimeTests(unittest.TestCase):
    def test_owned_mouse_button_is_released_without_foreground_check(self):
        game = GameWindow.__new__(GameWindow)
        game.holding = True
        game._closed = False
        with patch.object(game, "check", side_effect=RuntimeError("lost focus")) as check:
            with patch("fishing_auto.windows.win32api.mouse_event") as mouse:
                game.close()
                mouse.assert_called_once()
                check.assert_not_called()
        self.assertFalse(game.holding)

    def test_hold_cannot_press_when_window_checks_fail(self):
        game = GameWindow.__new__(GameWindow)
        game.holding = False
        with patch.object(game, "check", side_effect=RuntimeError("lost focus")):
            with patch("fishing_auto.windows.win32api.mouse_event") as mouse:
                with self.assertRaisesRegex(RuntimeError, "lost focus"):
                    game.hold(True, (.5, .5))
                mouse.assert_not_called()

    def test_f9_blocks_before_any_window_access(self):
        game = GameWindow.__new__(GameWindow)
        with patch.object(game, "stop_pressed", return_value=True):
            with patch("fishing_auto.windows.win32gui.IsWindow") as is_window:
                with self.assertRaisesRegex(RuntimeError, "F9"):
                    game.check()
                is_window.assert_not_called()

    def test_missing_profile_does_not_construct_windows_runtime(self):
        with patch("fishing_auto.windows.GameWindow") as game:
            with self.assertRaises(OSError):
                run(argparse.Namespace(profile="does-not-exist.json"))
            game.assert_not_called()

    def test_mocked_observe_only_session_never_sends_input(self):
        fixtures = test_vision.VisionTests("test_recognizes_distinct_scenes_and_tracks_horizontal_gauge")
        fixtures.setUp()
        try:
            profile_path = fixtures.directory / "profile.json"
            profile_path.write_text(json.dumps(fixtures.data), encoding="utf-8")
            args = argparse.Namespace(profile=profile_path, auto_cycle=False, rounds=1,
                                      sessions=str(fixtures.directory / "sessions"),
                                      observe_only=True, record=False, seconds=180, fps=60)
            frames = [fixtures.frames["playing"]] * 6 + [fixtures.frames["success"]] * 6
            current = [0.]
            def tick():
                current[0] += .01
                return current[0]
            with patch("fishing_auto.windows.GameWindow") as factory:
                game = factory.return_value
                game.capture.side_effect = frames
                with patch("fishing_auto.__main__.time.perf_counter", side_effect=tick), \
                     patch("fishing_auto.__main__.time.sleep"), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(run(args), 0)
                game.hold.assert_not_called()
                game.click.assert_not_called()
                game.close.assert_called_once()
            summary_files = list(Path(args.sessions).glob("*/summary.json"))
            summary = json.loads(summary_files[0].read_text(encoding="utf-8"))
            self.assertEqual(summary["mode"], "observe_only")
            self.assertFalse(summary["live_success_claim"])
            self.assertEqual(summary["successes"], 1)
        finally:
            fixtures.tearDown()

    def test_offline_video_replay_uses_real_timestamps_and_no_window_runtime(self):
        import cv2
        fixtures = test_vision.VisionTests("test_recognizes_distinct_scenes_and_tracks_horizontal_gauge")
        fixtures.setUp()
        try:
            profile_path = fixtures.directory / "profile.json"
            profile_path.write_text(json.dumps(fixtures.data), encoding="utf-8")
            video = fixtures.directory / "synthetic.avi"
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"FFV1"), 30, (400, 400))
            self.assertTrue(writer.isOpened())
            frames = [fixtures.frames["playing"]] * 6 + [fixtures.frames["failure"]] * 4
            try:
                for frame in frames:
                    writer.write(frame)
            finally:
                writer.release()
            timestamps = fixtures.directory / "frames.jsonl"
            timestamps.write_text("".join(json.dumps({"frame": i, "t": i * .04}) + "\n"
                                         for i in range(len(frames))), encoding="utf-8")
            output = fixtures.directory / "replay.jsonl"
            args = argparse.Namespace(profile=profile_path, video=video, timestamps=timestamps,
                                      output=output, rounds=1, auto_cycle=False)
            with patch("fishing_auto.windows.GameWindow") as game:
                with contextlib.redirect_stdout(io.StringIO()) as stdout:
                    replay(args)
                game.assert_not_called()
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["mode"], "offline_replay")
            self.assertFalse(report["live_success_claim"])
            self.assertEqual(report["failures"], 1)
            entries = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(entries[-1]["t"], .36)
            self.assertEqual(len(entries), len(frames))
            with self.assertRaises(FileExistsError), contextlib.redirect_stdout(io.StringIO()):
                replay(args)
        finally:
            fixtures.tearDown()


if __name__ == "__main__":
    unittest.main()
