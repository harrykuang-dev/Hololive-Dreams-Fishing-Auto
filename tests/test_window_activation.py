"""All Win32 calls are mocked; never activates or sends keys to a game."""
import unittest
from unittest.mock import Mock, patch
from auto_fishing import WindowCapture, run
from gui import FishingApp


class WindowActivationTests(unittest.TestCase):
    def window(self):
        window=WindowCapture.__new__(WindowCapture)
        window.hwnd=123
        return window

    def test_game_already_foreground_is_untouched_even_on_repeated_start(self):
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              patch('auto_fishing.win32gui.ShowWindow') as restore,
              patch('auto_fishing.win32gui.IsIconic') as iconic,
              patch('auto_fishing.win32api.keybd_event') as key,
              patch('auto_fishing.ctypes.windll.user32') as user32):
            self.window().activate()
            self.window().activate()
            restore.assert_not_called(); iconic.assert_not_called()
            key.assert_not_called(); user32.SetForegroundWindow.assert_not_called()
            user32.ShowWindowAsync.assert_not_called()

    def test_visible_background_game_keeps_window_state_without_alt(self):
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=999),
              patch('auto_fishing.win32gui.IsIconic',return_value=False),
              patch('auto_fishing.win32gui.ShowWindow') as restore,
              patch('auto_fishing.win32api.keybd_event') as key,
              patch('auto_fishing.ctypes.windll.user32') as user32):
            user32.SetForegroundWindow.return_value=1
            self.window().activate()
            restore.assert_not_called(); key.assert_not_called()
            user32.ShowWindowAsync.assert_not_called()
            user32.SetForegroundWindow.assert_called_once_with(123)

    def test_minimized_game_uses_async_restore_and_activation_failure_is_reported(self):
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=999),
              patch('auto_fishing.win32gui.IsIconic',return_value=True),
              patch('auto_fishing.ctypes.windll.user32') as user32):
            user32.ShowWindowAsync.return_value=1
            user32.SetForegroundWindow.return_value=1
            self.window().activate()
            user32.ShowWindowAsync.assert_called_once_with(123,9)
            user32.SetForegroundWindow.return_value=0
            with self.assertRaisesRegex(RuntimeError,'開始快捷鍵'):
                self.window().activate()
            user32.ShowWindowAsync.return_value=0
            with self.assertRaisesRegex(RuntimeError,'還原'):
                self.window().activate()

    def test_failed_startup_closes_window_without_constructing_mouse(self):
        with (patch('auto_fishing.WindowCapture') as capture,
              patch('auto_fishing.MouseController') as mouse):
            capture.return_value.activate.side_effect=RuntimeError('activation failed')
            with self.assertRaisesRegex(RuntimeError,'activation failed'):
                run(FishingApp.bot_args())
            capture.return_value.close.assert_called_once()
            mouse.assert_not_called()
