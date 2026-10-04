import json
from pathlib import Path
import unittest
import cv2
import numpy as np
from bot_vision import analyze
from palette_frames import palette_frames, retint
from test_bot_vision import close_x


class CharacterPaletteTests(unittest.TestCase):
    def test_all_62_control_tints_at_three_window_sizes(self):
        fixture = json.loads(Path(__file__).with_name('character_palettes.json').read_text(encoding='utf-8'))
        self.assertEqual(len(fixture['characters']),62)
        threads = cv2.getNumThreads()
        cv2.setNumThreads(1)
        try:
            for character in fixture['characters']:
                for scenario,frame,expected,point in palette_frames(character['colors'][3]):
                    for width,aspect in [(w,.6) for w in (500,900,1920)]+[(w,9/16) for w in (960,1280,1920)]:
                        with self.subTest(character=character['name'],scenario=scenario,width=width,aspect=aspect):
                            frame_small = cv2.resize(frame,(width,round(width*aspect)),interpolation=cv2.INTER_AREA)
                            detection = analyze(frame_small)
                            self.assertEqual(detection.scene,expected)
                            if point is not None:
                                self.assertIsNotNone(detection.action_button)
                                expected_point = np.array((point[0]*width/1000,point[1]*round(width*aspect)/600))
                                self.assertLess(np.linalg.norm(np.array(detection.action_button)-expected_point),width*.01)
        finally:
            cv2.setNumThreads(threads)

    def test_neutral_scenery_and_non_x_marks_are_rejected(self):
        for value in (63,95,117,180):
            frame = np.full((600,1000,3),value,np.uint8)
            self.assertEqual(analyze(frame).scene,'unknown')
        for mark in ('empty','plus','solid','slash'):
            frame = np.zeros((600,1000,3),np.uint8)
            cv2.rectangle(frame,(35,90),(975,590),(235,245,250),-1)
            close_x(frame,(955,55))
            cv2.circle(frame,(955,55),21,(255,255,255),-1)
            if mark=='plus':
                cv2.line(frame,(944,55),(966,55),(95,95,95),4)
                cv2.line(frame,(955,44),(955,66),(95,95,95),4)
            elif mark=='solid':
                cv2.rectangle(frame,(946,46),(964,64),(95,95,95),-1)
            elif mark=='slash':
                cv2.line(frame,(946,46),(964,64),(95,95,95),5)
            frame = retint(frame,'5F5F5F')
            with self.subTest(mark=mark):
                self.assertIsNone(analyze(frame).action_button)
