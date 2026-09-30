import unittest
from threading import Event
from unittest import mock
import numpy as np

import auto_fishing
from app_locale import GAME_LANGUAGES, text
from bot_vision import Detection
from gui import APP_VERSION, FishingApp


class GuiConfigurationTests(unittest.TestCase):
    def test_release_version_and_one_click_defaults(self):
        args = FishingApp.bot_args()
        self.assertEqual(APP_VERSION, "0.3.0")
        self.assertEqual(args.window_title, "hololive-Dreams")
        self.assertEqual(args.language, "auto")
        self.assertEqual(FishingApp.bot_args("zh-CN").language,"zh-CN")
        self.assertFalse(args.once)
        self.assertEqual(args.target_streak, 0)
        self.assertEqual(args.max_seconds, 0.0)
        self.assertEqual(args.pulse_hz, 7.0)
        self.assertIsNone(args.debug_dir)
        self.assertEqual(args.lead, .20)
        self.assertFalse(args.record)

    @mock.patch("auto_fishing.signal.signal")
    @mock.patch("auto_fishing.MouseController")
    @mock.patch("auto_fishing.WindowCapture")
    def test_windowed_runtime_does_not_require_stdout(
        self, _capture, _mouse, _signal
    ):
        stop_event = Event()
        stop_event.set()
        with mock.patch.object(auto_fishing.sys, "stdout", None):
            result = auto_fishing.run(
                FishingApp.bot_args(), stop_event=stop_event
            )
        self.assertEqual(result, 0)

    @mock.patch("auto_fishing.signal.signal")
    @mock.patch("auto_fishing.MouseController")
    @mock.patch("auto_fishing.WindowCapture")
    def test_runtime_messages_follow_selected_language(
        self, _capture, _mouse, _signal
    ):
        stop_event = Event()
        stop_event.set()
        for language in GAME_LANGUAGES.values():
            with self.subTest(language=language):
                messages = []
                with mock.patch.object(auto_fishing.sys, "stdout", None):
                    auto_fishing.run(FishingApp.bot_args(language),
                                     stop_event=stop_event, status_callback=messages.append)
                self.assertEqual(messages[0], text(language, "connected_window",
                                                   title="hololive-Dreams", language=language))
                self.assertIn(text(language, "final_stop", frames=0, seconds=0.0,
                                   rounds=0, catches=0, streak=0).split("0.0")[0], messages[-1])

    def test_target_streak_stops_after_ten_confirmed_results(self):
        args = FishingApp.bot_args("ja")
        args.target_streak = 10
        args.fps = 1000
        frame = np.zeros((900, 1600, 3), np.uint8)
        sequence = []
        for index in range(10):
            sequence.extend((Detection(track_present=True), Detection(catch_result=True)))
            if index < 9:
                sequence.append(Detection(tap=True))
        messages = []
        with (mock.patch("auto_fishing.WindowCapture") as capture,
              mock.patch("auto_fishing.MouseController"),
              mock.patch("auto_fishing.win32gui.GetForegroundWindow", return_value=123),
              mock.patch("auto_fishing.ReelTracker.update", return_value=None),
              mock.patch("auto_fishing.BiteGuard.update", side_effect=lambda d, _now: d.tap),
              mock.patch("auto_fishing.analyze", side_effect=sequence) as analyze,
              mock.patch("auto_fishing.signal.signal"),
              mock.patch.object(auto_fishing.sys, "stdout", None)):
            capture.return_value.hwnd = 123
            capture.return_value.grab.return_value = frame
            result = auto_fishing.run(args, status_callback=messages.append)
        self.assertEqual(result, 0)
        self.assertEqual(analyze.call_count, 29)
        self.assertIn(text("ja", "target_reached", target=10), messages)
        self.assertEqual(sum("釣果確認" in message for message in messages), 10)


if __name__ == "__main__":
    unittest.main()
