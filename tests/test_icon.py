"""Validate every packaged icon size, without modifying generated artwork."""
import unittest
from pathlib import Path
import tempfile
from PIL import Image
from tools.make_icon import make_icon, SIZES

class IconTests(unittest.TestCase):
    def test_pixel_icon_has_transparency_and_all_windows_sizes(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        with Image.open(assets/'fish-pixel.png') as source:
            colors={pixel for pixel in source.convert('RGBA').getdata() if pixel[3]}
        with Image.open(assets/'fish-pixel.ico') as icon:
            sizes={(n,n) for n in (16,24,32,48,64,128,256)}
            self.assertEqual(icon.ico.sizes(),sizes)
            for size in sizes:
                frame=icon.ico.getimage(size).convert('RGBA')
                self.assertEqual(frame.size,size)
                self.assertEqual(frame.getchannel('A').getextrema(),(0,255))
                # Nearest-neighbor icon conversion adds no interpolated colors.
                self.assertTrue({p for p in frame.getdata() if p[3]}<=colors)

    def test_current_icon_has_exact_dpi_sizes_and_crisp_pixels(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        with Image.open(assets/'fish-clear.png') as source:
            colors={pixel for pixel in source.convert('RGBA').getdata() if pixel[3]}
        with Image.open(assets/'fish-clear.ico') as icon:
            self.assertEqual(icon.ico.sizes(),{(n,n) for n in SIZES})
            self.assertTrue({16,20,24,28,32,40,48,56,64,80,96}<=set(SIZES))
            for n in SIZES:
                frame=icon.ico.getimage((n,n)).convert('RGBA')
                alpha_min,alpha_max=frame.getchannel('A').getextrema()
                self.assertEqual(alpha_min,0)
                # Generated PNG interiors can have alpha 254; nearest-neighbor
                # preserves this instead of inventing opaque source pixels.
                self.assertGreaterEqual(alpha_max,250)
                left,top,right,bottom=frame.getbbox()
                self.assertGreaterEqual(right-left,n*.75)
                self.assertGreaterEqual(bottom-top,int(n*.7))
                self.assertTrue({p for p in frame.getdata() if p[3]}<=colors)
                self.assertEqual(frame.getpixel((0,0))[3],0)
                self.assertEqual(frame.getpixel((n-1,n-1))[3],0)

    def test_packager_reproduces_each_explicit_frame(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        with tempfile.TemporaryDirectory() as folder:
            output=make_icon(assets/'fish-clear.png',Path(folder)/'icon.ico',pixel=True)
            with Image.open(output) as rebuilt, Image.open(assets/'fish-clear.ico') as shipped:
                for n in SIZES:
                    self.assertEqual(rebuilt.ico.getimage((n,n)).tobytes(),
                                     shipped.ico.getimage((n,n)).tobytes())
