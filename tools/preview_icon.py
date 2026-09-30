"""Render existing ICO frames at native size and 3x for visual inspection.

This is a QA contact sheet, not a source asset or an artwork editing tool.
"""
from pathlib import Path
from PIL import Image, ImageDraw


def preview():
    repo = Path(__file__).resolve().parents[1]
    sheet = Image.new('RGB',(860,734),'#e5e5e5')
    draw = ImageDraw.Draw(sheet)
    columns = [('OLD / light','fish-pixel.ico','#ffffff'),
               ('NEW / light','fish-clear.ico','#ffffff'),
               ('OLD / dark','fish-pixel.ico','#202020'),
               ('NEW / dark','fish-clear.ico','#202020')]
    for col,(label,name,bg) in enumerate(columns):
        x = col*215
        draw.text((x+12,10),label,fill='#202020')
        with Image.open(repo/'assets'/name) as icon:
            for row,size in enumerate((16,24,32,48)):
                y = 34+row*175
                draw.rectangle((x+4,y,x+210,y+168),fill=bg)
                fg = '#202020' if bg=='#ffffff' else '#ffffff'
                draw.text((x+12,y+8),f'{size}px / native + 3x',fill=fg)
                frame = icon.ico.getimage((size,size)).convert('RGBA')
                sheet.paste(frame,(x+12,y+40),frame)
                zoom = frame.resize((size*3,size*3),Image.Resampling.NEAREST)
                sheet.paste(zoom,(x+64,y+24),zoom)
    output = repo/'build'/'icon-comparison.png'
    output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output)
    print(output)


if __name__=='__main__': preview()
