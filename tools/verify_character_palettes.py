"""Write a reproducible offline character palette verification matrix."""
import argparse
import csv
import json
from pathlib import Path
import sys
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'tests')]
from app_locale import GAME_LANGUAGES
from bot_vision import analyze
from palette_frames import palette_frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    fixture = json.loads((ROOT/'tests/character_palettes.json').read_text(encoding='utf-8'))
    results = []
    cv2.setNumThreads(1)
    for character in fixture['characters']:
        for scenario,frame,expected,point in palette_frames(character['colors'][3]):
            checks = [(w,'auto',.6) for w in (500,900,1920)] + [(w,'auto',9/16) for w in (960,1280,1920)] + [(900,c,.6) for c in GAME_LANGUAGES.values()]
            for width,language,aspect in checks:
                detection = analyze(cv2.resize(frame,(width,round(width*aspect)),interpolation=cv2.INTER_AREA),language)
                passed = detection.scene==expected
                if point is not None:
                    expected_point = np.array((point[0]*width/1000,point[1]*round(width*aspect)/600))
                    passed = passed and detection.action_button is not None and np.linalg.norm(np.array(detection.action_button)-expected_point)<width*.01
                results.append(dict(id=character['id'],name=character['name'],rgb=character['colors'][3],scenario=scenario,width=width,height=round(width*aspect),language=language,expected=expected,actual=detection.scene,passed=bool(passed)))
    with (args.output/'character-palette-matrix.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    summary = dict(source=fixture['source'],characters=len(fixture['characters']),cases=len(results),failed=sum(not r['passed'] for r in results),limits=fixture['note'])
    (args.output/'character-palette-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    return int(summary['failed']>0)


if __name__=='__main__':
    raise SystemExit(main())
