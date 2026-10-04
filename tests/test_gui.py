import unittest
import os
import tempfile
from pathlib import Path
from threading import Event
from unittest import mock
import numpy as np

import auto_fishing
from app_locale import GAME_LANGUAGES, text
from bot_vision import Detection
from gui import APP_VERSION, FishingApp


class GuiConfigurationTests(unittest.TestCase):
    def test_diagnostic_link_creates_missing_folder_before_opening(self):
        app=FishingApp.__new__(FishingApp)
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'HololiveFishingAuto'/'sessions'
            with mock.patch.object(app,'diagnostic_base',return_value=folder),mock.patch('gui.os.startfile') as explorer:
                self.assertEqual(app.open_diagnostics(),'break')
                self.assertTrue(folder.is_dir())
                explorer.assert_called_once_with(str(folder.resolve()))

    def test_diagnostic_link_permission_error_shows_error_without_opening(self):
        app=FishingApp.__new__(FishingApp)
        app.root=mock.Mock()
        app._developer_help_dialog=None
        folder=mock.Mock()
        folder.resolve.return_value=folder
        folder.mkdir.side_effect=PermissionError('Access denied')
        with (mock.patch.object(app,'diagnostic_base',return_value=folder),
              mock.patch.object(app,'language_code',return_value='zh-TW'),
              mock.patch('gui.os.startfile') as explorer,mock.patch('gui.messagebox.showerror') as error):
            app.open_diagnostics()
            explorer.assert_not_called()
            error.assert_called_once()
    def test_diagnostic_path_follows_each_local_windows_account(self):
        for local in ('C:/Users/Alice/AppData/Local','D:/Profiles/Bob/AppData/Local'):
            with self.subTest(local=local),mock.patch.dict(os.environ,{'LOCALAPPDATA':local}):
                self.assertEqual(FishingApp.diagnostic_base(),Path(local)/'HololiveFishingAuto'/'sessions')

    def test_press_rearms_if_windows_button_was_released_externally(self):
        mouse = auto_fishing.MouseController.__new__(auto_fishing.MouseController)
        mouse.window = mock.Mock(hwnd=123)
        mouse.held = True
        mouse._move_client = mock.Mock()
        with (mock.patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              mock.patch('auto_fishing.win32api.GetAsyncKeyState',return_value=0),
              mock.patch('auto_fishing.win32api.mouse_event') as event):
            mouse.press((100,200))
        event.assert_called_once_with(auto_fishing.win32con.MOUSEEVENTF_LEFTDOWN,0,0)
        self.assertTrue(mouse.held)

    def test_press_does_not_repeat_down_when_windows_is_already_holding(self):
        mouse = auto_fishing.MouseController.__new__(auto_fishing.MouseController)
        mouse.window = mock.Mock(hwnd=123)
        mouse.held = True
        with (mock.patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              mock.patch('auto_fishing.win32api.GetAsyncKeyState',return_value=0x8000),
              mock.patch('auto_fishing.win32api.mouse_event') as event):
            mouse.press((100,200))
        event.assert_not_called()

    def test_release_version_and_one_click_defaults(self):
        args = FishingApp.bot_args()
        self.assertEqual(APP_VERSION, "1.1")
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
        self.assertEqual(args.target_catches, 0)
        self.assertEqual(args.stop_hotkey, 'F9')

    def test_target_counts_fish_not_streak_and_reports_each_catch_once(self):
        args = FishingApp.bot_args('zh-TW')
        args.target_catches = 2
        args.fps = 1000
        # Ignore the result from before startup, ignore duplicate cards,
        # and still reach the total target after an unconfirmed middle round.
        sequence = [Detection(catch_result=True), Detection(track_present=True),
                    Detection(catch_result=True), Detection(catch_result=True),
                    Detection(tap=True), Detection(track_present=True),
                    Detection(tap=True), Detection(track_present=True),
                    Detection(catch_result=True)]
        progress, messages = [], []
        with (mock.patch('auto_fishing.WindowCapture') as capture,
              mock.patch('auto_fishing.MouseController') as mouse,
              mock.patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              mock.patch('auto_fishing.win32api.GetAsyncKeyState',return_value=0),
              mock.patch('auto_fishing.ReelTracker.update',return_value=None),
              mock.patch('auto_fishing.BiteGuard.update',side_effect=lambda d,_now:d.tap),
              mock.patch('auto_fishing.analyze',side_effect=sequence) as analyze,
              mock.patch('auto_fishing.signal.signal'),
              mock.patch.object(auto_fishing.sys,'stdout',None)):
            capture.return_value.hwnd = 123
            capture.return_value.grab.return_value = np.zeros((900,1600,3),np.uint8)
            auto_fishing.run(args,status_callback=messages.append,progress_callback=progress.append)
        self.assertEqual(analyze.call_count,len(sequence))
        self.assertEqual(progress,[{'catches':1,'rounds':1,'streak':1},
                                   {'catches':2,'rounds':3,'streak':1}])
        self.assertIn(text('zh-TW','catch_target_reached',target=2),messages)
        mouse.return_value.close.assert_called_once()

    def test_custom_shortcut_stops_before_capture(self):
        args = FishingApp.bot_args('en')
        args.stop_hotkey = 'Ctrl+Alt+Q'
        messages = []
        with (mock.patch('auto_fishing.WindowCapture') as capture,
              mock.patch('auto_fishing.MouseController') as mouse,
              mock.patch('auto_fishing.win32gui.GetForegroundWindow') as foreground,
              mock.patch('auto_fishing.win32api.GetAsyncKeyState',return_value=0x8000),
              mock.patch('auto_fishing.signal.signal'),
              mock.patch.object(auto_fishing.sys,'stdout',None)):
            auto_fishing.run(args,status_callback=messages.append)
        capture.return_value.grab.assert_not_called()
        foreground.assert_not_called()
        mouse.return_value.close.assert_called_once()
        self.assertIn(text('en','hotkey_stop',hotkey=args.stop_hotkey),messages)

    def test_invalid_settings_do_not_construct_window_runtime(self):
        for key,target in (('Win+Q',0),('F9',-1)):
            args = FishingApp.bot_args()
            args.stop_hotkey,args.target_catches = key,target
            with mock.patch('auto_fishing.WindowCapture') as capture:
                with self.assertRaises(ValueError): auto_fishing.run(args)
                capture.assert_not_called()

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
