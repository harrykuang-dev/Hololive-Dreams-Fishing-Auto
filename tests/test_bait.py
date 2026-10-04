"""Recovery tests: blinking warnings, uncertain selection and input priority."""
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch
import cv2
import numpy as np
from bait_control import BaitSwitcher
from bait_vision import BaitObservation, observe_bait
from bot_vision import Detection


class BaitControlTests(unittest.TestCase):
    depleted = BaitObservation(result=True, exhausted=True, dim_continue=True, change_point=(100,450), continue_visible=True)
    blank = BaitObservation()
    healthy = BaitObservation(result=True, change_point=(100,450), continue_visible=True)
    dialog = BaitObservation(dialog=True, infinite_point=(222,151), confirm_point=(798,463))

    def test_card_before_buttons_blocks_every_action(self):
        c = BaitSwitcher(True)
        card = replace(self.healthy, change_point=None, continue_visible=False)
        for t in (0,.24,.9,1.5):
            d=c.update(card,t)
            self.assertTrue(d.managed)
            self.assertEqual(d.phase,'settling')
            self.assertIsNone(d.action)
        self.assertTrue(c.update(self.healthy,1.6).managed)
        self.assertTrue(c.update(self.healthy,2.2).managed)
        self.assertFalse(c.update(self.healthy,2.26).managed)

    def test_probe_waits_for_actual_buttons_and_result_animation(self):
        c = BaitSwitcher(True)
        card=replace(self.depleted,exhausted=False,change_point=None,continue_visible=False,continue_point=(748,463))
        self.assertIsNone(c.update(card,0).action)
        ready=replace(card,change_point=(100,450),continue_visible=True)
        self.assertIsNone(c.update(ready,.9).action)
        self.assertIsNone(c.update(ready,1.54).action)
        self.assertIsNone(c.update(ready,1.56).action)
        self.assertIsNone(c.update(ready,1.8).action)
        self.assertEqual(c.update(ready,1.82).action,(748,463))

    def test_blinking_warning_during_settle_is_retained(self):
        c = BaitSwitcher(True)
        c.update(self.depleted,0)
        c.update(self.healthy,.6)
        d=c.update(self.healthy,1.6)
        self.assertTrue(d.managed)
        self.assertTrue(c.latched)
        self.assertEqual(c.update(self.healthy,2.3).action,(100,450))

    def test_ready_old_result_does_not_fail_settle_timeout(self):
        c = BaitSwitcher(True)
        c.result_since = c.buttons_since = 0.
        self.assertFalse(c.update(self.healthy,9.).failed)

    def test_disabled_preserves_normal_navigation(self):
        c = BaitSwitcher()
        for t in range(30):
            self.assertFalse(c.update(self.depleted,t,6).managed)

    def test_one_warning_frame_latches_through_blink_and_scene_disappearance(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        self.assertIsNone(c.update(self.depleted,0).action)
        for t in (.1,.3,.6):
            self.assertTrue(c.update(self.blank,t).managed)
        o = replace(self.healthy, dim_continue=False)
        self.assertEqual(c.update(o,.7).action,(100,450))
        self.assertTrue(c.latched)

    def test_unverified_change_button_holds_without_clicking_continue(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        o = replace(self.depleted,exhausted=False,change_point=None)
        for t in (0,.3,1.,2.,7.):
            d = c.update(o,t)
            self.assertTrue(d.managed)
            self.assertIsNone(d.action)
        self.assertTrue(c.update(o,8.1).failed)

    def test_persistently_dim_result_opens_bait_without_red_warning(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        o = replace(self.depleted, exhausted=False)
        for t in (0,.4,1.,1.49):
            self.assertIsNone(c.update(o,t).action)
        self.assertEqual(c.update(o,1.51).action,(100,450))
        self.assertTrue(c.latched)
        self.assertTrue(c.update(self.healthy,1.6).managed)
        self.assertEqual(c.phase,'opening')

    def test_continue_probe_is_once_then_warning_can_blink(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        o = replace(self.depleted, exhausted=False, continue_point=(748,463))
        self.assertIsNone(c.update(o,0).action)
        self.assertEqual(c.update(o,.3).action,(748,463))
        self.assertIsNone(c.update(o,.5).action)
        self.assertIsNone(c.update(replace(o,exhausted=True),.7).action)
        self.assertTrue(c.update(self.blank,1.).managed)
        self.assertEqual(c.update(o,1.51).action,(100,450))
        self.assertTrue(c.latched)

    def test_existing_continue_click_counts_as_probe(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        o = replace(self.depleted, exhausted=False, continue_point=(748,463))
        c.update(o,0,1)
        self.assertIsNone(c.update(o,.3).action)
        self.assertEqual(c.update(o,1.51).action,(100,450))

    def test_interrupted_dim_frames_do_not_establish_depletion(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        o = replace(self.depleted, exhausted=False)
        c.update(o,0)
        c.update(o,1.)
        c.update(self.healthy,1.1)
        c.update(o,1.4)
        self.assertIsNone(c.update(o,2.).action)
        self.assertFalse(c.latched)

    def test_transient_dim_recovers_only_after_quiet_interval(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        c.update(replace(self.depleted,exhausted=False),0)
        self.assertTrue(c.update(self.healthy,.1).managed)
        self.assertTrue(c.update(self.healthy,1.59).managed)
        self.assertTrue(c.update(self.healthy,1.61).managed)
        self.assertFalse(c.update(self.healthy,1.7).managed)

    def test_repeated_continue_cannot_reset_retry_limit_during_animation(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        c.update(self.healthy,0,2)
        self.assertTrue(c.update(self.healthy,.4,0).managed)
        self.assertTrue(c.update(self.healthy,1.51,0).failed)

    def test_selection_and_confirm_require_stable_infinite_selection(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        c.update(self.depleted,0)
        self.assertEqual(c.update(self.depleted,.7).action,(100,450))
        # A wrong bait's enabled confirm is never clicked.
        self.assertIsNone(c.update(self.dialog,.8).action)
        self.assertEqual(c.update(self.dialog,1.91).action,(222,151))
        selected = replace(self.dialog,selected_infinite=True)
        self.assertIsNone(c.update(selected,2.).action)
        self.assertIsNone(c.update(self.dialog,2.2).action)
        self.assertIsNone(c.update(selected,2.3).action)
        self.assertIsNone(c.update(selected,2.81).action)  # global spacing
        self.assertEqual(c.update(selected,3.12).action,(798,463))
        self.assertTrue(c.update(self.blank,3.3).managed)
        self.assertTrue(c.update(self.healthy,3.4).managed)
        self.assertTrue(c.update(replace(self.healthy,exhausted=True),3.8).managed)
        self.assertTrue(c.update(self.healthy,4.).managed)
        self.assertTrue(c.update(self.healthy,4.66).managed)
        self.assertFalse(c.update(self.healthy,4.7).managed)

    def test_wrong_dialog_cannot_close_x_or_click_other_bait(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        c.update(self.depleted,0)
        c.update(self.depleted,.7)
        for t in (1.,2.,4.,7.):
            self.assertIsNone(c.update(self.blank,t).action)
        self.assertTrue(c.update(self.blank,8.71).failed)

    def test_open_attempts_bounded_and_spaced(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        actions=[]
        for i in range(81):
            d=c.update(self.depleted,i*.1)
            if d.action: actions.append(i*.1)
        self.assertEqual(len(actions),3)
        self.assertTrue(all(b-a >= 1.19 for a,b in zip(actions,actions[1:])))

    def test_return_requires_visible_enabled_continue(self):
        c = BaitSwitcher(True, result_settle=0, button_settle=0)
        c.enter('returning',0)
        for t in (0,1.,3.,7.):
            self.assertIsNone(c.update(self.depleted,t).action)
        self.assertTrue(c.update(self.depleted,8.1).failed)


class BaitVisionTests(unittest.TestCase):
    def result(self, warning=True, active=False, scale=1):
        f=np.full((506,900,3),100,np.uint8)
        cv2.rectangle(f,(717,446),(780,480),(70,30,50),-1)
        cv2.putText(f,'GO',(722,469),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255) if active else (185,185,185),2)
        if warning:
            cv2.fillPoly(f,[np.array([(446,443),(435,464),(457,464)])],(30,40,230))
            cv2.line(f,(446,449),(446,456),(255,255,255),2)
            cv2.circle(f,(446,460),1,(255,255,255),-1)
        return cv2.resize(f,None,fx=scale,fy=scale), Detection(catch_result=True,action_button=(748*scale,463*scale))

    def test_alert_and_disabled_glyphs_at_several_sizes(self):
        for scale in (.75,1,1.5,2):
            f,d=self.result(scale=scale)
            o=observe_bait(f,d)
            self.assertTrue(o.exhausted,scale)
            self.assertTrue(o.dim_continue,scale)
            f,d=self.result(warning=False,active=True,scale=scale)
            o=observe_bait(f,d)
            self.assertFalse(o.exhausted,scale)
            self.assertFalse(o.dim_continue,scale)

    def test_red_fish_without_white_exclamation_does_not_trigger(self):
        f,d=self.result(warning=False,active=True)
        cv2.ellipse(f,(446,454),(12,9),0,0,360,(30,40,230),-1)
        self.assertFalse(observe_bait(f,d).exhausted)
        cv2.circle(f,(446,452),3,(255,255,255),-1)
        self.assertFalse(observe_bait(f,d).exhausted)

    def test_alert_is_only_used_on_confirmed_result_card(self):
        f,_=self.result()
        o=observe_bait(f,Detection())
        self.assertFalse(o.exhausted)
        self.assertFalse(o.dim_continue)


    def dialog_frame(self, tint=(210,110,30), selected=False, infinity=True):
        f=np.full((506,900,3),100,np.uint8)
        cv2.rectangle(f,(150,53),(751,108),tint,-1)
        cv2.rectangle(f,(150,109),(751,430),(240,240,240),-1)
        cv2.rectangle(f,(508,87),(731,416),(255,255,255),-1)
        cv2.circle(f,(222,151),26,(40,180,235),-1)
        if infinity:
            cv2.ellipse(f,(229,201),(3,2),0,0,360,tint,1)
            cv2.ellipse(f,(234,201),(3,2),0,0,360,tint,1)
        else:
            cv2.ellipse(f,(231,201),(2,3),0,0,360,tint,1)
        if selected:
            for x,y in ((183,116),(247,116),(183,173),(247,173)):
                cv2.rectangle(f,(x,y),(x+15,y+17),tint,-1)
            cv2.circle(f,(620,164),42,(40,180,235),-1)
        cv2.rectangle(f,(724,444),(871,481),(255,255,255),-1)
        cv2.rectangle(f,(727,447),(868,478),tint,-1)
        return f

    def test_dialog_selection_at_all_published_character_tints(self):
        import json
        from pathlib import Path
        palettes=json.loads(Path(__file__).with_name('character_palettes.json').read_text(encoding='utf-8'))['characters']
        for character in palettes:
            color=character['colors'][3].lstrip('#')
            bgr=tuple(int(color[i:i+2],16) for i in (4,2,0))
            for selected in (False,True):
                o=observe_bait(self.dialog_frame(bgr,selected),Detection())
                self.assertTrue(o.dialog,(character['name'],selected))
                self.assertEqual(o.selected_infinite,selected,character['name'])
                self.assertIsNotNone(o.confirm_point,character['name'])

    def test_quantity_zero_cannot_be_mistaken_for_infinity(self):
        self.assertFalse(observe_bait(self.dialog_frame(infinity=False),Detection()).dialog)

    def test_missing_dough_art_cannot_be_mistaken_for_bait_dialog(self):
        f=self.dialog_frame();cv2.rectangle(f,(184,116),(259,189),(240,240,240),-1)
        self.assertFalse(observe_bait(f,Detection()).dialog)


class BaitRuntimeTests(unittest.TestCase):
    def test_bait_owns_dialog_input_before_generic_close_and_continue(self):
        import auto_fishing
        from gui import FishingApp
        args=FishingApp.bot_args('en'); args.auto_bait=True
        stop=Mock(); stop.is_set.side_effect=[False]*9+[True]
        # Simulated clock .4 s between screenshots, no real waits or game input.
        clock=iter([0.] + [i*.5+offset for i in range(9) for offset in (0.,.005,.01,.02,.025)] + [5.])
        exhausted=BaitObservation(result=True,exhausted=True,dim_continue=True,change_point=(100,450), continue_visible=True)
        wrong=BaitObservation(dialog=True,infinite_point=(222,151),confirm_point=(798,463))
        selected=replace(wrong,selected_infinite=True)
        observations=[exhausted]*3+[wrong]*3+[selected]*3
        detections=[Detection(catch_result=True,scene='result_continue',action_button=(748,463))]*3+[Detection(scene='item_detail',action_button=(733,61))]*6
        with (patch('auto_fishing.WindowCapture') as capture,
              patch('auto_fishing.MouseController') as mouse,
              patch('auto_fishing.BaitSwitcher',side_effect=lambda enabled: BaitSwitcher(enabled,result_settle=0,button_settle=0)),
              patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
              patch('auto_fishing.stop_hotkey_pressed',return_value=False),
              patch('auto_fishing.signal.signal'),patch('auto_fishing.time.sleep'),
              patch.object(auto_fishing.sys,'stdout',None),
              patch('auto_fishing.time.perf_counter',side_effect=lambda:next(clock)),
              patch('auto_fishing.analyze',side_effect=detections),
              patch('auto_fishing.observe_bait',side_effect=observations)):
            capture.return_value.hwnd=123
            capture.return_value.grab.return_value=np.zeros((506,900,3),np.uint8)
            auto_fishing.run(args,stop_event=stop,status_callback=lambda _:None)
            points=[call.args[0] for call in mouse.return_value.click.call_args_list]
            self.assertIn((100,450),points)
            self.assertIn((222,151),points)
            self.assertNotIn((748,463),points)
            self.assertNotIn((733,61),points)
            mouse.return_value.click_gameplay.assert_not_called()
