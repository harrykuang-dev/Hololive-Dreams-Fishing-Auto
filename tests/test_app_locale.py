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

    def test_generic_language_labels(self):
        expected={'zh-TW':'語言 / Language','zh-CN':'语言 / Language',
                  'en':'Language','ja':'言語 / Language','id':'Bahasa / Language','ko':'언어 / Language'}
        for code,label in expected.items():
            self.assertEqual(text(code,'game_language'),label)

    def test_developer_help_matches_confirmed_wording(self):
        expected = ('啟用後會儲存狀態截圖、魚獲卡片及追蹤與耗時作爲診斷資料，用於定位與排查異常。資料不會自動上傳。'
                    '\n\n診斷資料位於：\nFOLDER\n\n'
                    '每次運行會建立以時間命名的資料夾。如遇異常，可透過下方項目地址聯繫作者，並提供問題描述及診斷資料。開啟開發者模式會增加效能負擔。')
        actual = text('zh-TW','developer_help',path='FOLDER')
        self.assertTrue(actual.startswith(expected))
        self.assertIn('diagnostics-YYYY-MM-DD_HH-MM-SS.zip',actual)


if __name__ == "__main__":
    unittest.main()
