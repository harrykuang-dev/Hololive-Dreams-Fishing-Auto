"""Validate the six user guides and their navigation without network access."""
import re
import unittest
from pathlib import Path
from app_locale import GAME_LANGUAGES


ROOT=Path(__file__).resolve().parents[1]
GUIDES=('README.md','README.zh-CN.md','README.en.md','README.ja.md','README.ko.md','README.id.md')


class ReadmeTests(unittest.TestCase):
    def test_each_supported_language_has_a_complete_guide(self):
        self.assertEqual(len(GUIDES),len(GAME_LANGUAGES))
        for name in GUIDES:
            content=(ROOT/name).read_text(encoding='utf-8')
            self.assertGreater(len(content.splitlines()),45,name)
            for language in GAME_LANGUAGES:
                self.assertIn(language,content,name)
            for guide in GUIDES:
                self.assertIn(f']({guide})',content,name)

    def test_relative_document_links_resolve(self):
        for name in (*GUIDES,'docs/DEVELOPMENT.md'):
            path=ROOT/name
            content=path.read_text(encoding='utf-8')
            for target in re.findall(r'\]\(([^)]+)\)',content):
                if '://' in target or target.startswith('#'):
                    continue
                self.assertTrue((path.parent/target.split('#')[0]).is_file(),(name,target))

    def test_readmes_are_product_guides_not_release_history(self):
        for name in GUIDES:
            content=(ROOT/name).read_text(encoding='utf-8')
            self.assertNotRegex(content,r'\b0\.\d+|RELEASE-[\d.]')
            self.assertIn('releases/latest',content)
            self.assertIn('issues)',content)

    def test_all_guides_cover_the_current_user_workflow(self):
        for name in GUIDES:
            content=(ROOT/name).read_text(encoding='utf-8')
            for term in ('Hololive-Dreams-Fishing-Auto-v1.0.exe','F9','`0`','16:9',
                         '%LOCALAPPDATA%\\HololiveFishingAuto\\sessions\\','SHA-256'):
                self.assertIn(term,content,(name,term))

    def test_all_guides_link_known_issues(self):
        target='https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md'
        for name in GUIDES:
            content=(ROOT/name).read_text(encoding='utf-8')
            self.assertIn(f']({target})',content.splitlines()[2],name)
            self.assertEqual(content.count('KNOWN_ISSUES.md'),1,name)
            self.assertNotIn('Fuwawa',content,name)
