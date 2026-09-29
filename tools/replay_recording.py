"""Replay desktop recordings offline using their visible game title bar."""
import argparse
import csv
import json
from pathlib import Path
import sys
import subprocess
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from auto_fishing import analyze, annotate


def client_crop(frame, previous=None):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array((0, 0, 230)), np.array((180, 30, 255)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 150), np.uint8))
    stats = cv2.connectedComponentsWithStats(mask)[2]
    candidates = [tuple(map(int, s[:4])) for s in stats[1:]
                  if 1100 < s[2] < 1400 and 18 <= s[3] <= 35]
    rect = candidates[-1] if candidates else previous
    if not rect:
        return None, previous
    x, y, w, h = rect
    return frame[y + h:y + h + round(w * 9 / 16), x:x + w], rect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('video')
    parser.add_argument('output')
    parser.add_argument('--hz', type=float, default=10)
    parser.add_argument('--compare-baseline', action='store_true')
    parser.add_argument('--baseline-ref', default='0.1.0', help='Trusted local Git revision used for comparison')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stride = max(1, round(fps / args.hz))
    last_rect = None
    counts = {}
    old_analyze = None
    metrics = dict(track_frames=0,complete_markers=0,baseline_track_frames=0,baseline_complete_markers=0)
    if args.compare_baseline:
        source = subprocess.run(['git','show',f'{args.baseline_ref}:auto_fishing.py'],capture_output=True,
                                text=True,encoding='utf-8',check=True).stdout
        module = types.ModuleType('offline_baseline')
        sys.modules[module.__name__] = module
        namespace = module.__dict__
        exec(compile(source,'baseline_auto_fishing.py','exec'),namespace)
        old_analyze = namespace['analyze']
    with (output / 'replay.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['seconds', 'track', 'player_y', 'bar_h', 'fish_y', 'scene', 'action_x', 'action_y'])
        for index in range(count):
            if not cap.grab():
                break
            if index % stride:
                continue
            ok, desktop = cap.retrieve()
            if not ok:
                continue
            frame, last_rect = client_crop(desktop, last_rect)
            if frame is None or frame.size == 0:
                continue
            d = analyze(frame)
            metrics['track_frames'] += int(d.track_present)
            metrics['complete_markers'] += int(d.minigame)
            if old_analyze:
                old = old_analyze(frame)
                metrics['baseline_track_frames'] += int(old.track_present)
                metrics['baseline_complete_markers'] += int(old.minigame)
            scene = getattr(d, 'scene', '') or ('reel' if d.minigame else 'tap' if d.tap else 'button' if d.action_button else 'unknown')
            counts[scene] = counts.get(scene, 0) + 1
            writer.writerow([round(index / fps, 3), int(d.track_present),
                             d.player_center[1] if d.player_center else '',
                             d.player_box[3] if d.player_box else '',
                             d.fish_center[1] if d.fish_center else '', scene,
                             *(d.action_button or ('', ''))])
            if index % round(fps) < stride or (d.track_present and not d.minigame):
                cv2.imwrite(str(output / f'{index / fps:07.2f}_{scene}.jpg'), annotate(frame, d, scene))
    cap.release()
    print(json.dumps(counts))
    print(json.dumps(metrics))
    (output/'metrics.json').write_text(json.dumps({'scenes':counts,**metrics},indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
