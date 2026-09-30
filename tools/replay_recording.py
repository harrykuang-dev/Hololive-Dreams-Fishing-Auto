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
from bot_control import Navigation, BiteGuard


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
    crop_group = parser.add_mutually_exclusive_group()
    crop_group.add_argument('--client-rect', type=int, nargs=4, metavar=('X','Y','W','H'),
                        help='Explicit client rectangle for occluded or unusually sized desktop recordings')
    crop_group.add_argument('--client-quad', type=float, nargs=8,
                            help='Photographed game corners: TL, TR, BR, BL (x y pairs); offline analysis only')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stride = max(1, round(fps / args.hz))
    last_rect = None
    perspective = None
    if args.client_quad:
        perspective = cv2.getPerspectiveTransform(
            np.float32(args.client_quad).reshape(4,2),
            np.float32([[0,0],[1599,0],[1599,899],[0,899]]))
    counts = {}
    navigation,bite_guard = Navigation(),BiteGuard()
    old_analyze = None
    old_navigation, old_bite_guard = Navigation(), BiteGuard()
    metrics = dict(track_frames=0,complete_markers=0,tap_frames=0,
                   baseline_track_frames=0,baseline_complete_markers=0,baseline_tap_frames=0,
                   hypothetical_navigation_clicks=0,hypothetical_hook_clicks=0,
                   catch_result_frames=0,baseline_catch_result_frames=0,
                   baseline_navigation_clicks=0,baseline_hook_clicks=0)
    if args.compare_baseline:
        vision_source = subprocess.run(['git','show',f'{args.baseline_ref}:bot_vision.py'],
                                       capture_output=True,text=True,encoding='utf-8')
        source = vision_source.stdout if vision_source.returncode==0 else subprocess.run(
            ['git','show',f'{args.baseline_ref}:auto_fishing.py'],capture_output=True,
            text=True,encoding='utf-8',check=True).stdout
        module = types.ModuleType('offline_baseline')
        sys.modules[module.__name__] = module
        namespace = module.__dict__
        exec(compile(source,'baseline_auto_fishing.py','exec'),namespace)
        old_analyze = namespace['analyze']
    with (output / 'replay.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['seconds', 'track', 'player_y', 'bar_h', 'fish_y', 'scene', 'action_x', 'action_y',
                         'hypothetical_navigation_click','hypothetical_hook_click'])
        for index in range(count):
            if not cap.grab():
                break
            if index % stride:
                continue
            ok, desktop = cap.retrieve()
            if not ok:
                continue
            if perspective is not None:
                frame = cv2.warpPerspective(desktop,perspective,(1600,900))
            elif args.client_rect:
                x,y,w,h = args.client_rect
                frame = desktop[y:y+h,x:x+w]
            else:
                frame, last_rect = client_crop(desktop, last_rect)
            if frame is None or frame.size == 0:
                continue
            d = analyze(frame)
            # Simulation only: these controllers return decisions; this tool
            # never constructs a Windows input runtime or sends clicks.
            action = navigation.update(d,index/fps)
            nav_click = isinstance(action,tuple) and not d.track_present
            hook_click = bite_guard.update(d,index/fps) and not d.track_present and not nav_click
            metrics['hypothetical_navigation_clicks'] += int(nav_click)
            metrics['hypothetical_hook_clicks'] += int(hook_click)
            metrics['track_frames'] += int(d.track_present)
            metrics['complete_markers'] += int(d.minigame)
            metrics['tap_frames'] += int(d.tap)
            metrics['catch_result_frames'] += int(d.catch_result)
            if old_analyze:
                old = old_analyze(frame)
                # Early baselines predate scene labels used by Navigation.
                if not hasattr(old, 'scene'):
                    old.scene = 'action' if old.action_button else 'unknown'
                metrics['baseline_track_frames'] += int(old.track_present)
                metrics['baseline_complete_markers'] += int(old.minigame)
                metrics['baseline_tap_frames'] += int(old.tap)
                metrics['baseline_catch_result_frames'] += int(getattr(old,'catch_result',False))
                old_action = old_navigation.update(old,index/fps)
                old_nav_click = isinstance(old_action,tuple) and not old.track_present
                metrics['baseline_navigation_clicks'] += int(old_nav_click)
                metrics['baseline_hook_clicks'] += int(old_bite_guard.update(old,index/fps)
                    and not old.track_present and not old_nav_click)
            scene = getattr(d, 'scene', '') or ('reel' if d.minigame else 'tap' if d.tap else 'button' if d.action_button else 'unknown')
            counts[scene] = counts.get(scene, 0) + 1
            writer.writerow([round(index / fps, 3), int(d.track_present),
                             d.player_center[1] if d.player_center else '',
                             d.player_box[3] if d.player_box else '',
                             d.fish_center[1] if d.fish_center else '', scene,
                             *(d.action_button or ('', '')),int(nav_click),int(hook_click)])
            if index % round(fps) < stride or (d.track_present and not d.minigame):
                cv2.imwrite(str(output / f'{index / fps:07.2f}_{scene}.jpg'), annotate(frame, d, scene))
    cap.release()
    print(json.dumps(counts))
    print(json.dumps(metrics))
    (output/'metrics.json').write_text(json.dumps({'scenes':counts,**metrics},indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
