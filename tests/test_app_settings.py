import unittest
from app_settings import FishingCounter,parse_stop_hotkey,stop_hotkey_pressed,captured_hotkey

class SettingsTests(unittest.TestCase):
    def test_every_begin_run_resets_count_and_duplicate_updates_do_not_add(self):
        counter = FishingCounter()
        counter.begin_run()
        self.assertEqual(counter.update(2),2)
        self.assertEqual(counter.update(2),2)
        counter.begin_run()
        self.assertEqual(counter.total,0)
        self.assertEqual(counter.run_catches,0)
        self.assertEqual(counter.update(3),3)
        self.assertEqual(counter.remaining(10),7)
        self.assertEqual(counter.remaining(0),0)
        self.assertEqual(FishingCounter().total,0)

    def test_function_key_and_combo_parsing(self):
        self.assertEqual(parse_stop_hotkey('f9'),((),0x78))
        self.assertEqual(parse_stop_hotkey('Ctrl+Alt+Q'),((0x11,0x12),ord('Q')))
        self.assertEqual(parse_stop_hotkey('Esc'),((),0x1b))
        self.assertEqual(parse_stop_hotkey('Q'),((),ord('Q')))
        self.assertEqual(parse_stop_hotkey('F24'),((),0x87))
        self.assertEqual(parse_stop_hotkey('Num1'),((),0x61))
        for value in ('F25','Ctrl+Ctrl+Q','Win+Q','Ctrl+',''):
            with self.subTest(value=value),self.assertRaises(ValueError):
                parse_stop_hotkey(value)

    def test_capture_physical_keys_and_modifiers(self):
        self.assertEqual(captured_hotkey('F9',0,0x78),'F9')
        self.assertEqual(captured_hotkey('q',0x20004,0x51),'Ctrl+Alt+Q')
        self.assertEqual(captured_hotkey('exclam',1,0x31),'Shift+1')
        self.assertEqual(captured_hotkey('KP_1',0,0x61),'Num1')
        self.assertEqual(captured_hotkey('Escape',0,0x1B),'Esc')
        self.assertEqual(captured_hotkey('colon',1,0xBA),'Shift+Semicolon')
        self.assertIsNone(captured_hotkey('Control_L',4,0x11))
        self.assertIsNone(captured_hotkey('Super_L',0,0x5B))
        self.assertIsNone(captured_hotkey('q',0x40,0x51))

    def test_shortcut_requires_all_modifiers_and_a_down_key(self):
        down={0x11,0x12,ord('Q')}
        get=lambda vk:0x8000 if vk in down else 0
        self.assertTrue(stop_hotkey_pressed('Ctrl+Alt+Q',get))
        down.remove(0x12)
        self.assertFalse(stop_hotkey_pressed('Ctrl+Alt+Q',get))
        self.assertFalse(stop_hotkey_pressed('F9',lambda _vk:1))
