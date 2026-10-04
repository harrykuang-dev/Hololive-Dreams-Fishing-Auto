import unittest
from unittest.mock import Mock, patch

from auto_fishing import MouseController


class GameplayInputTests(unittest.TestCase):
    def setUp(self):
        self.mouse = MouseController.__new__(MouseController)
        self.mouse.held = False
        self.mouse.window = Mock(hwnd=123)
        self.mouse.window._capture_rect = (100,200,1700,1100)

    def test_tap_and_reel_reuse_any_existing_client_cursor(self):
        self.mouse.click = Mock()
        self.mouse.press = Mock()
        with patch('auto_fishing.win32api.GetCursorPos',return_value=(200,400)):
            self.mouse.click_gameplay(1600,900)
            self.mouse.press_gameplay(1600,900)
        self.mouse.click.assert_called_once_with((100,200),duration=.045)
        self.mouse.press.assert_called_once_with((100,200))

    def test_outside_cursor_uses_client_centre(self):
        with patch('auto_fishing.win32api.GetCursorPos',return_value=(1900,400)):
            self.assertEqual(self.mouse.gameplay_point(1600,900),(800,450))

    def test_existing_position_avoids_setcursorpos_but_still_checks_occlusion(self):
        self.mouse.window.screen_point.return_value = (200,400)
        with (patch('auto_fishing.win32api.GetCursorPos',return_value=(200,400)),
              patch('auto_fishing.win32gui.WindowFromPoint',return_value=456),
              patch('auto_fishing.win32gui.GetAncestor',return_value=123),
              patch('auto_fishing.win32api.SetCursorPos') as move):
            self.mouse._move_client((100,200))
            move.assert_not_called()
        with (patch('auto_fishing.win32gui.WindowFromPoint',return_value=456),
              patch('auto_fishing.win32gui.GetAncestor',return_value=999),
              patch('auto_fishing.win32api.mouse_event') as event):
            with self.assertRaisesRegex(RuntimeError,'遮擋'):
                self.mouse.click_gameplay(1600,900)
            event.assert_not_called()

    def test_bait_scroll_checks_focus_and_occlusion_before_wheel_input(self):
        self.mouse._move_client=Mock()
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              patch('auto_fishing.win32api.mouse_event') as event):
            self.mouse.scroll_up((340,250))
            self.mouse._move_client.assert_called_once_with((340,250))
            event.assert_called_once_with(0x0800,0,0,960)
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=999),
              patch('auto_fishing.win32api.mouse_event') as event):
            self.mouse.scroll_up((340,250))
            event.assert_not_called()
        self.mouse._move_client.side_effect=RuntimeError('occluded')
        with patch('auto_fishing.win32api.mouse_event') as event:
            with self.assertRaisesRegex(RuntimeError,'occluded'):
                self.mouse.scroll_up((340,250))
            event.assert_not_called()

    def test_moved_window_and_lost_focus_cannot_press(self):
        self.mouse.window.screen_point.side_effect = RuntimeError('moved window')
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              patch('auto_fishing.win32api.GetCursorPos',return_value=(200,400)),
              patch('auto_fishing.win32api.mouse_event') as event):
            with self.assertRaisesRegex(RuntimeError,'moved window'):
                self.mouse.press_gameplay(1600,900)
            event.assert_not_called()
        with (patch('auto_fishing.win32gui.GetForegroundWindow',return_value=999),
              patch('auto_fishing.win32api.mouse_event') as event):
            self.mouse.press_gameplay(1600,900)
            event.assert_not_called()


if __name__ == '__main__':
    unittest.main()
