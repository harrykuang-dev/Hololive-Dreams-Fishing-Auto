"""Private, local contact sheets; recordings are never copied to the repository."""
import argparse
from pathlib import Path
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('video')
    parser.add_argument('output')
    parser.add_argument('--step', type=float, default=5)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    sheet = None
    for index, seconds in enumerate(np.arange(args.start, min(args.end or duration, duration), args.step)):
        cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        cv2.imwrite(str(output / f'frame_{seconds:07.2f}.jpg'), frame)
        tile = cv2.resize(frame, (480, 270))
        cv2.rectangle(tile, (0, 0), (160, 27), (0, 0, 0), -1)
        cv2.putText(tile, f'{seconds:.2f}s', (5, 21), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 255, 255), 1)
        slot = index % 20
        if slot == 0:
            sheet = np.zeros((5 * 270, 4 * 480, 3), np.uint8)
        row, col = divmod(slot, 4)
        sheet[row * 270:(row + 1) * 270, col * 480:(col + 1) * 480] = tile
        cv2.imwrite(str(output / f'sheet_{index // 20:02d}.jpg'), sheet)
    cap.release()
    print(f'{duration:.2f}s; sheets: {output}')


if __name__ == '__main__':
    main()
