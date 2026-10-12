"""Package transparent artwork as ICO; pixel mode keeps each size unblurred."""
import argparse
from pathlib import Path
from PIL import Image

# Include native 125/150/175/200% title-bar and taskbar sizes. Windows should
# select an exact frame instead of scaling a neighbouring ICO image.
SIZES = (16,20,24,28,32,40,48,56,60,64,72,80,96,128,256)


def make_icon(source_path,output_path,pixel=False,crop=False):
    source = Image.open(source_path).convert('RGBA')
    if source.getchannel('A').getextrema()[0] != 0:
        raise ValueError('Source must already have transparent pixels')
    frames = []
    if pixel or crop:
        alpha = source.getchannel('A')
        # Fit the visible glyph, not nearly transparent extraction specks.
        # Only the exported frames are cropped; the source artwork is preserved.
        bounds = alpha.point(lambda value:255 if value>=128 else 0).getbbox() if crop else alpha.getbbox()
        if bounds is None: raise ValueError('Source has no visible artwork')
        source = source.crop(bounds)
    for size in SIZES:
        frame = Image.new('RGBA',(size,size))
        artwork = source.copy()
        margin = 1 if pixel or crop else max(1,round(size/32))
        artwork.thumbnail((size-margin*2,size-margin*2),
                          Image.Resampling.NEAREST if pixel else Image.Resampling.LANCZOS)
        frame.alpha_composite(artwork,((size-artwork.width)//2,(size-artwork.height)//2))
        frames.append(frame)
    # Explicit pre-sized frames avoid Pillow's default smooth ICO resampling.
    frames[-1].save(output_path,format='ICO',sizes=[(n,n) for n in SIZES],append_images=frames[:-1])
    return Path(output_path).resolve()


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('output')
    parser.add_argument('--pixel',action='store_true')
    parser.add_argument('--crop',action='store_true',help='Fit visible artwork tightly; keep antialiased resizing')
    args = parser.parse_args()
    print(make_icon(args.source,args.output,args.pixel,args.crop))
