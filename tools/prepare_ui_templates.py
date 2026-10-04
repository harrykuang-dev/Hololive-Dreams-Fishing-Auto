"""Generate the compact TAP shape from a locally extracted toolkit sprite.

No network access, game input or modification. Pass ui_230_txt_tap.png from
hololive-toolkit's extractor output; the game atlas must be unpacked first.
"""
import argparse
from pathlib import Path
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sprite',type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'assets/vision/tap_letters.png')
    args=parser.parse_args()
    sprite=cv2.imdecode(np.fromfile(args.sprite,np.uint8),cv2.IMREAD_UNCHANGED)
    if sprite is None or sprite.ndim!=3 or sprite.shape[2]!=4:
        raise ValueError('Expected the RGBA TAP sprite')
    hsv=cv2.cvtColor(sprite[:,:,:3],cv2.COLOR_BGR2HSV)
    letters=cv2.bitwise_or(cv2.inRange(hsv,np.array((0,0,200)),np.array((179,65,255))),
                          cv2.inRange(hsv,np.array((20,35,190)),np.array((40,255,255))))
    letters[sprite[:,:,3]<128]=0
    x,y,w,h=cv2.boundingRect(letters)
    if not w or not h:
        raise ValueError('No TAP letter art found')
    template=cv2.resize(letters[y:y+h,x:x+w],(144,round(144*h/w)),interpolation=cv2.INTER_AREA)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    ok,encoded=cv2.imencode('.png',template)
    if not ok:
        raise OSError('Template encoding failed')
    args.output.write_bytes(encoded.tobytes())
    print(f'{args.output}: {template.shape[1]}x{template.shape[0]}, {encoded.nbytes} bytes')


if __name__=='__main__':
    main()
