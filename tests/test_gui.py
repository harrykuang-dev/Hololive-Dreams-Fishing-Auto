import unittest
from threading import Event
from unittest import mock

import auto_fishing
from gui import APP_VERSION, FishingApp


class GuiConfigurationTests(unittest.TestCase):
    def test_release_version_and_one_click_defaults(self):
        args = FishingApp.bot_args()
        self.assertEqual(APP_VERSION, "0.2.5")
        self.assertEqual(args.window_title, "hololive-Dreams")
        self.assertEqual(args.language, "auto")
        self.assertEqual(FishingApp.bot_args("zh-CN").language,"zh-CN")
        self.assertFalse(args.once)
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


if __name__ == "__main__":
    unittest.main()
