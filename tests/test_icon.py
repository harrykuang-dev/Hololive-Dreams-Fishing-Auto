"""Validate every packaged icon size, without modifying generated artwork."""
import unittest
from pathlib import Path
import tempfile
from PIL import Image
from tools.make_icon import make_icon, SIZES

class IconTests(unittest.TestCase):
    def test_hook_icon_keeps_transparency_and_reproducible_windows_frames(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        with Image.open(assets/'fishing-hook.png') as source:
            self.assertEqual(source.mode,'RGBA')
            self.assertEqual(source.getchannel('A').getextrema(),(0,255))
        with tempfile.TemporaryDirectory() as folder:
            output=make_icon(assets/'fishing-hook.png',Path(folder)/'hook.ico',crop=True)
            with Image.open(output) as rebuilt, Image.open(assets/'fishing-hook.ico') as shipped:
                self.assertEqual(shipped.ico.sizes(),{(n,n) for n in SIZES})
                for n in SIZES:
                    frame=shipped.ico.getimage((n,n)).convert('RGBA')
                    self.assertEqual(frame.tobytes(),rebuilt.ico.getimage((n,n)).convert('RGBA').tobytes())
                    self.assertEqual(frame.getpixel((0,0))[3],0)
                    self.assertGreaterEqual(frame.getchannel('A').getextrema()[1],250)
