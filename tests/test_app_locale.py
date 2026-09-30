import string
import unittest

from app_locale import GAME_LANGUAGES, TEXT, text
from gui import FishingApp


class LocaleTests(unittest.TestCase):
    def test_game_language_names_and_codes(self):
        self.assertEqual(GAME_LANGUAGES, {
            "日本語": "ja", "English": "en", "Indonesian": "id",
            "한국어": "ko", "繁體中文": "zh-TW", "简体中文": "zh-CN",
        })
        self.assertEqual(set(TEXT), set(GAME_LANGUAGES.values()))
        for code in GAME_LANGUAGES.values():
            self.assertEqual(FishingApp.bot_args(code).language, code)

    def test_all_messages_exist_with_matching_format_fields(self):
        formatter = string.Formatter()
        baseline = TEXT["zh-TW"]
        for code, catalogue in TEXT.items():
            with self.subTest(language=code):
                self.assertEqual(set(catalogue), set(baseline))
                for key, template in baseline.items():
                    fields = {name for _, name, _, _ in formatter.parse(template) if name}
                    translated = {name for _, name, _, _ in formatter.parse(catalogue[key]) if name}
                    self.assertEqual(translated, fields, key)
                    values = {name: 1 for name in fields}
                    self.assertTrue(text(code, key, **values))

    def test_legacy_auto_keeps_traditional_chinese(self):
        self.assertEqual(text("auto", "idle"), text("zh-TW", "idle"))


if __name__ == "__main__":
    unittest.main()
