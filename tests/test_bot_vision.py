import unittest
import cv2
import numpy as np
from bot_vision import analyze


def color(h,s,v):
    return tuple(int(x) for x in cv2.cvtColor(np.uint8([[[h,s,v]]]),cv2.COLOR_HSV2BGR)[0,0])


def track_frame(bar_h=65,bar_y=260,fish_y=280):
    f = np.zeros((600,1000,3),np.uint8)
    gold = color(18,200,150)
    cv2.rectangle(f,(665,30),(755,550),gold,-1)
    cv2.rectangle(f,(678,44),(714,535),color(108,150,230),-1)
    cv2.rectangle(f,(679,bar_y),(713,bar_y+bar_h),color(28,180,250),-1)
    cv2.ellipse(f,(696,fish_y),(25,15),0,0,360,color(97,240,250),-1)
    return f


def close_x(frame,point):
    cyan = color(99,210,245)
    cv2.circle(frame,point,25,cyan,4)
    cv2.circle(frame,point,21,(255,255,255),-1)
    cv2.line(frame,(point[0]-9,point[1]-9),(point[0]+9,point[1]+9),cyan,4)
    cv2.line(frame,(point[0]+9,point[1]-9),(point[0]-9,point[1]+9),cyan,4)


class TrackVisionTests(unittest.TestCase):
    def test_overlap_does_not_move_bar_center_to_visible_color_centroid(self):
        d = analyze(track_frame(90,250,315))
        self.assertTrue(d.minigame)
        self.assertAlmostEqual(d.player_center[1],295,delta=4)
        self.assertAlmostEqual(d.player_box[3],90,delta=4)

    def test_small_bar_and_bright_reflection_are_detected(self):
        f = track_frame(32,260,220)
        cv2.rectangle(f,(679,260),(713,271),color(28,45,255),-1)
        d = analyze(f)
        self.assertTrue(d.minigame)
        self.assertAlmostEqual(d.player_box[3],32,delta=4)

    def test_pale_cyan_lane_does_not_merge_into_the_fish_sprite(self):
        f = track_frame()
        cv2.rectangle(f,(680,44),(712,261),color(98,100,255),-1)
        d = analyze(f)
        self.assertTrue(d.minigame)
        self.assertAlmostEqual(d.fish_center[1],280,delta=3)
        self.assertLess(d.fish_box[3],40)

    def test_marker_colored_scenery_without_track_is_not_gameplay(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(680,250),(715,320),color(28,200,250),-1)
        cv2.ellipse(f,(696,280),(25,15),0,0,360,color(97,240,250),-1)
        d = analyze(f)
        self.assertFalse(d.minigame)
        self.assertIsNone(d.player_center)
        self.assertIsNone(d.fish_center)


class PopupVisionTests(unittest.TestCase):
    def test_book_x_connected_to_cyan_background_is_detected(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(0,0),(999,110),color(99,210,245),-1)
        cv2.rectangle(f,(35,110),(975,590),(235,245,250),-1)
        close_x(f,(955,55))
        for scale in (1,.75,.5):
            with self.subTest(scale=scale):
                d = analyze(cv2.resize(f,None,fx=scale,fy=scale))
                self.assertEqual(d.scene,'encyclopedia')
                self.assertAlmostEqual(d.action_button[0],955*scale,delta=3)
                self.assertAlmostEqual(d.action_button[1],55*scale,delta=3)

        # A circular white hole without an X is not a close button.
        cv2.circle(f,(955,55),21,(255,255,255),-1)
        self.assertIsNone(analyze(f).action_button)

    def test_book_closes_its_x_but_ready_menu_x_is_not_clicked(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(35,90),(975,590),(235,245,250),-1)
        close_x(f,(955,55))
        d = analyze(f)
        self.assertEqual(d.scene,'encyclopedia')
        self.assertAlmostEqual(d.action_button[0],955,delta=3)
        f[:] = 0
        cv2.rectangle(f,(620,240),(780,480),(255,255,255),-1)
        close_x(f,(955,55))
        self.assertIsNone(analyze(f).action_button)

    def test_item_details_use_inset_x_not_background_continue(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(240,150),(770,500),(250,250,250),-1)
        close_x(f,(760,155))
        cv2.rectangle(f,(760,535),(930,575),color(101,210,245),-1)
        self.assertEqual(analyze(f).scene,'item_detail')

    def test_rod_tip_closes_x_not_go_to_upgrade_shop(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(165,75),(830,530),(250,250,250),-1)
        cv2.rectangle(f,(190,190),(530,390),color(95,150,235),-1)
        close_x(f,(815,85))
        cv2.rectangle(f,(650,470),(800,515),color(99,220,245),-1)
        d = analyze(f)
        self.assertEqual(d.scene,'item_detail')
        self.assertLess(d.action_button[1],150)

    def test_reward_requires_get_evidence_and_clicks_blank_space(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(0,190),(999,410),color(95,140,245),-1)
        self.assertNotEqual(analyze(f).scene,'reward')
        for text,x in zip('GET',(430,473,516)):
            cv2.putText(f,text,(x,92),cv2.FONT_HERSHEY_SIMPLEX,1.5,(255,255,255),4)
        d = analyze(f)
        self.assertEqual(d.scene,'reward')
        self.assertGreater(d.action_button[1],410)
        self.assertFalse(d.tap)

    def test_reward_fade_cannot_mistake_purple_item_for_tap(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(0,190),(999,410),color(95,140,245),-1)
        cv2.circle(f,(500,300),24,color(155,220,245),-1)
        d = analyze(f)
        self.assertEqual(d.scene,'overlay_animation')
        self.assertFalse(d.tap)
        self.assertIsNone(d.action_button)

    def test_material_reward_prefers_continue_over_blank_fish_list(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(0,190),(999,410),color(95,140,245),-1)
        for text,x in zip('GET',(430,473,516)):
            cv2.putText(f,text,(x,92),cv2.FONT_HERSHEY_SIMPLEX,1.5,(255,255,255),4)
        cv2.rectangle(f,(785,525),(945,575),color(99,210,245),-1)
        d = analyze(f)
        self.assertEqual(d.scene,'reward_continue')
        self.assertGreater(d.action_button[0],785)
        self.assertGreater(d.action_button[1],525)
        self.assertFalse(d.tap)

        # An inset item-details modal can retain GET and Continue behind it.
        cv2.rectangle(f,(240,150),(770,500),(250,250,250),-1)
        close_x(f,(760,155))
        self.assertEqual(analyze(f).scene,'item_detail')

    def test_reward_animation_does_not_click_background_continue(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(0,190),(999,410),color(95,140,245),-1)
        cv2.rectangle(f,(785,525),(945,575),color(99,210,245),-1)
        d = analyze(f)
        self.assertEqual(d.scene,'overlay_animation')
        self.assertIsNone(d.action_button)

    def test_button_aspect_rejects_rightmost_scenery(self):
        f = np.zeros((600,1000,3),np.uint8)
        cyan = color(99,210,245)
        cv2.rectangle(f,(750,535),(920,575),cyan,-1)
        cv2.rectangle(f,(925,500),(990,590),cyan,-1)
        d = analyze(f)
        self.assertEqual(d.scene,'action')
        self.assertLess(d.action_button[0],920)


if __name__ == '__main__':
    unittest.main()
