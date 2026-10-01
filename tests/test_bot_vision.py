import unittest
import cv2
import numpy as np
from bot_vision import analyze
from app_locale import GAME_LANGUAGES


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


def close_x(frame,point,hue=99):
    cyan = color(hue,210,245)
    cv2.circle(frame,point,25,cyan,4)
    cv2.circle(frame,point,21,(255,255,255),-1)
    cv2.line(frame,(point[0]-9,point[1]-9),(point[0]+9,point[1]+9),cyan,4)
    cv2.line(frame,(point[0]+9,point[1]-9),(point[0]-9,point[1]+9),cyan,4)


def action_button(frame,start,end,text=True,hue=99,value=245,white_value=255):
    x,y = start
    x1,y1 = end
    r = (y1-y)//2
    white = (white_value,)*3
    for inset,c in ((0,white),(3,color(hue,210,value))):
        cv2.rectangle(frame,(x+r,y+inset),(x1-r,y1-inset),c,-1)
        cv2.circle(frame,(x+r,y+r),r-inset,c,-1)
        cv2.circle(frame,(x1-r,y+r),r-inset,c,-1)
    if text:
        cv2.putText(frame,'NEXT',(x+round((x1-x)*.30),y+round((y1-y)*.70)),
                    cv2.FONT_HERSHEY_SIMPLEX,(y1-y)/65,white,2)


def bite_frame(text=True, bang=True, outline=True):
    f = np.zeros((600,1000,3),np.uint8)
    cv2.circle(f,(500,410),37,(255,255,255),-1)
    cv2.circle(f,(500,410),32,color(155,150,250),-1)
    if bang:
        cv2.rectangle(f,(495,389),(505,410),(255,255,255),-1)
        cv2.circle(f,(500,424),6,(255,255,255),-1)
    if text:
        if outline:
            cv2.putText(f,'TAP!',(430,310),cv2.FONT_HERSHEY_SIMPLEX,2,color(117,220,255),10)
        cv2.putText(f,'TAP!',(430,310),cv2.FONT_HERSHEY_SIMPLEX,2,color(30,200,255),4)
    return f


class BiteVisionTests(unittest.TestCase):
    def test_same_gameplay_art_works_for_every_supported_language(self):
        for code in GAME_LANGUAGES.values():
            with self.subTest(language=code):
                self.assertTrue(analyze(bite_frame(), code).tap)
                self.assertTrue(analyze(track_frame(), code).minigame)

    def test_bite_requires_all_three_independent_ui_features(self):
        for scale in (1,.75,.5):
            with self.subTest(scale=scale):
                self.assertTrue(analyze(cv2.resize(bite_frame(),None,fx=scale,fy=scale)).tap)
        self.assertFalse(analyze(bite_frame(text=False)).tap)
        self.assertFalse(analyze(bite_frame(bang=False)).tap)
        self.assertFalse(analyze(bite_frame(outline=False)).tap)

    def test_pink_ice_reflections_cannot_trigger_hook(self):
        f = np.zeros((600,1000,3),np.uint8)
        for x,y in ((420,350),(495,390),(570,435)):
            cv2.ellipse(f,(x,y),(23,21),0,0,360,color(155,160,245),-1)
            cv2.line(f,(x-15,y),(x+12,y+8),(255,255,255),3)
        self.assertFalse(analyze(f).tap)

    def test_prompt_entrance_scale_uses_badge_relative_text_geometry(self):
        f = bite_frame()
        for scale in (.7,.85,1):
            transform = np.float32([[scale,0,500*(1-scale)],[0,scale,410*(1-scale)]])
            with self.subTest(scale=scale):
                self.assertTrue(analyze(cv2.warpAffine(f,transform,(1000,600))).tap)

    def test_near_white_letter_highlight_does_not_hide_real_tap(self):
        f = bite_frame()
        hsv = cv2.cvtColor(f,cv2.COLOR_BGR2HSV)
        yellow = cv2.inRange(hsv,np.array((20,35,195)),np.array((38,255,255)))>0
        yellow[290:] = False
        f[yellow] = color(30,15,255)
        self.assertTrue(analyze(f).tap)


class TrackVisionTests(unittest.TestCase):
    def test_pale_fish_is_detected_without_accepting_plain_lane(self):
        f = track_frame()
        cv2.ellipse(f,(696,280),(25,15),0,0,360,color(97,95,250),-1)
        d = analyze(f)
        self.assertTrue(d.minigame)
        self.assertAlmostEqual(d.fish_center[1],280,delta=3)
        cv2.rectangle(f,(680,44),(712,264),color(98,100,255),-1)
        self.assertAlmostEqual(analyze(f).fish_center[1],280,delta=3)
        cv2.rectangle(f,(669,262),(723,298),color(18,200,150),-1)
        cv2.rectangle(f,(678,44),(714,535),color(98,95,250),-1)
        self.assertIsNone(analyze(f).fish_center)

    def test_low_saturation_bar_highlight_keeps_full_height(self):
        f = track_frame(65,260,230)
        cv2.rectangle(f,(679,260),(713,290),color(28,25,255),-1)
        d = analyze(f)
        self.assertAlmostEqual(d.player_box[3],65,delta=4)

    def test_character_button_hues_require_ui_structure(self):
        for hue in (0,15,35,60,90,120,150,175):
            with self.subTest(hue=hue):
                f = np.zeros((600,1000,3),np.uint8)
                action_button(f,(750,525),(945,574),hue=hue)
                self.assertEqual(analyze(f).scene,'action')
                f = np.zeros_like(f)
                action_button(f,(750,525),(945,574),hue=hue,text=False)
                self.assertIsNone(analyze(f).action_button)

    def test_character_x_hues_keep_modal_close_priority(self):
        for hue in (0,15,35,60,90,120,150,175):
            with self.subTest(hue=hue):
                f = np.zeros((600,1000,3),np.uint8)
                cv2.rectangle(f,(30,65),(970,585),color(25,20,250),-1)
                close_x(f,(930,55),hue=hue)
                action_button(f,(750,525),(945,574),hue=hue)
                self.assertEqual(analyze(f).scene,'encyclopedia')

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
    def test_blue_violet_continue_keeps_border_and_glyph_requirements(self):
        for hue in (99,110,120,130):
            f = np.zeros((600,1000,3),np.uint8)
            action_button(f,(750,535),(920,575),hue=hue,value=205,white_value=212)
            for scale in (1,.75,.5):
                with self.subTest(hue=hue,scale=scale):
                    d = analyze(cv2.resize(f,None,fx=scale,fy=scale))
                    self.assertEqual(d.scene,'action')
                    self.assertAlmostEqual(d.action_button[0],835*scale,delta=3)
            f[:] = 0
            action_button(f,(750,535),(920,575),text=False,hue=hue,value=205,white_value=212)
            self.assertIsNone(analyze(f).action_button)
            f[:] = 0
            cv2.rectangle(f,(750,535),(920,575),color(hue,210,205),-1)
            cv2.line(f,(750,532),(920,532),(212,212,212),3)
            cv2.line(f,(750,578),(920,578),(212,212,212),3)
            cv2.putText(f,'NEXT',(790,562),cv2.FONT_HERSHEY_SIMPLEX,.6,(212,212,212),2)
            self.assertIsNone(analyze(f).action_button)

    def test_dim_fish_card_still_requires_get_badge(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(520,30),(960,550),(212,212,212),-1)
        self.assertFalse(analyze(f).catch_result)
        self.assertIsNone(analyze(f).action_button)
        for letter,x in zip('GET!',(530,577,624,671)):
            cv2.putText(f,letter,(x,88),cv2.FONT_HERSHEY_SIMPLEX,1.5,color(120,180,205),9)
            cv2.putText(f,letter,(x,88),cv2.FONT_HERSHEY_SIMPLEX,1.5,color(30,60,215),4)
        self.assertTrue(analyze(f).catch_result)

    def test_blue_violet_modal_x_still_precedes_continue(self):
        f = np.zeros((600,1000,3),np.uint8)
        action_button(f,(750,535),(920,575),hue=120)
        cv2.rectangle(f,(35,90),(975,520),(235,245,250),-1)
        close_x(f,(955,55),hue=120)
        d = analyze(f)
        self.assertEqual(d.scene,'encyclopedia')
        self.assertLess(d.action_button[1],100)

    def test_fish_get_card_confirms_catch_and_has_safe_continue_fallback(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(520,30),(960,550),(245,245,245),-1)
        for letter,x in zip('GET!',(530,577,624,671)):
            cv2.putText(f,letter,(x,88),cv2.FONT_HERSHEY_SIMPLEX,1.5,
                        color(117,230,250),9)
            cv2.putText(f,letter,(x,88),cv2.FONT_HERSHEY_SIMPLEX,1.5,
                        color(30,210,250),4)
        for language in ('auto','zh-CN','zh-TW'):
            with self.subTest(language=language):
                d = analyze(f,language)
                self.assertTrue(d.catch_result)
                self.assertEqual(d.scene,'result_continue')
                self.assertAlmostEqual(d.action_button[0],830,delta=2)
        no_card = f.copy()
        no_card[96:550,520:960] = 0
        self.assertFalse(analyze(no_card).catch_result)

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

    def test_snowy_ready_screen_must_start_not_close_top_right_x(self):
        f = np.full((600,1000,3),245,np.uint8)
        cv2.rectangle(f,(580,0),(999,599),color(110,70,210),-1)
        # Pale cards occupy most of the right panel, as in the report.
        cv2.rectangle(f,(615,155),(969,245),(245,245,245),-1)
        cv2.rectangle(f,(615,280),(969,485),(245,245,245),-1)
        close_x(f,(955,45))
        action_button(f,(700,520),(890,572))
        for scale in (1,.75,.5):
            with self.subTest(scale=scale):
                d = analyze(cv2.resize(f,None,fx=scale,fy=scale))
                self.assertEqual(d.scene,'action')
                self.assertAlmostEqual(d.action_button[0],795*scale,delta=3)
                self.assertGreater(d.action_button[1],500*scale)
        # Without a verified Start button, do nothing instead of clicking X.
        f[500:] = color(110,70,210)
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
        action_button(f,(785,525),(945,575))
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
        action_button(f,(785,525),(945,575))
        d = analyze(f)
        self.assertEqual(d.scene,'overlay_animation')
        self.assertIsNone(d.action_button)

    def test_button_aspect_rejects_rightmost_scenery(self):
        f = np.zeros((600,1000,3),np.uint8)
        cyan = color(99,210,245)
        action_button(f,(750,535),(920,575))
        cv2.rectangle(f,(925,500),(990,590),cyan,-1)
        d = analyze(f)
        self.assertEqual(d.scene,'action')
        self.assertLess(d.action_button[0],920)

    def test_cyan_ocean_rectangle_is_not_continue(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(750,535),(920,575),color(99,210,245),-1)
        self.assertIsNone(analyze(f).action_button)
        action_button(f,(750,535),(920,575),text=False)
        self.assertIsNone(analyze(f).action_button)

    def test_outlined_continue_with_text_survives_scaling(self):
        f = np.zeros((600,1000,3),np.uint8)
        action_button(f,(750,535),(920,575))
        for scale in (1,.75,.5):
            with self.subTest(scale=scale):
                d=analyze(cv2.resize(f,None,fx=scale,fy=scale))
                self.assertEqual(d.scene,'action')
                self.assertAlmostEqual(d.action_button[0],835*scale,delta=3)

    def test_white_waves_and_glyph_like_spots_without_side_borders_are_rejected(self):
        f = np.zeros((600,1000,3),np.uint8)
        cv2.rectangle(f,(750,535),(920,575),color(99,210,245),-1)
        cv2.line(f,(750,532),(920,532),(255,255,255),3)
        cv2.line(f,(750,578),(920,578),(255,255,255),3)
        cv2.putText(f,'NEXT',(790,562),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),2)
        self.assertIsNone(analyze(f).action_button)


if __name__ == '__main__':
    unittest.main()
