import unittest
from bot_control import ReelTracker, ReelControl, Navigation, Tracking, BiteGuard, CatchLedger
from bot_vision import Detection


def observation(player=350, fish=350, bar=80, track=True):
    return Detection(track_present=track,player_center=(690,player),
                     fish_center=(690,fish),player_box=(675,int(player-bar/2),30,bar))


class TemporalControlTests(unittest.TestCase):
    def test_occlusion_is_bounded_and_track_disappearance_releases(self):
        tracker = ReelTracker()
        tracker.update(observation(),10,700)
        predicted = tracker.update(Detection(track_present=True),10.08,700)
        self.assertTrue(predicted.predicted)
        self.assertIsNone(tracker.update(Detection(track_present=True),10.15,700))
        self.assertIsNone(tracker.update(Detection(),10.16,700))
        self.assertIsNone(tracker.last)

    def test_impossible_single_frame_jump_does_not_reverse_target(self):
        tracker = ReelTracker()
        tracker.update(observation(),0,700)
        tracker.update(observation(352,351),.04,700)
        rejected = tracker.update(observation(100,620),.08,700)
        self.assertTrue(rejected.predicted)
        self.assertLess(abs(rejected.fish-351),10)
        restored = tracker.update(observation(353,352),.12,700)
        self.assertFalse(restored.predicted)
        self.assertLess(abs(restored.fish_velocity),100)

    def test_occluded_small_bar_keeps_height_instead_of_shifting_centroid(self):
        tracker = ReelTracker()
        tracker.update(observation(350,350,60),0,700)
        partial = observation(363,350,34)
        result = tracker.update(partial,.04,700)
        self.assertEqual(result.bar_height,60)
        self.assertAlmostEqual(result.player,350)

    def test_momentum_and_small_bar_trigger_early_braking(self):
        controller = ReelControl(.20)
        # Still below the fish but moving upward rapidly: release before
        # reaching its centre instead of continuing a long hold.
        pressed,mode,_ = controller.decide(Tracking(365,350,40,-300,0),700)
        self.assertFalse(pressed)
        self.assertEqual(mode,'release')
        pressed,mode,_ = controller.decide(Tracking(380,350,40,0,0),700)
        self.assertTrue(pressed)
        self.assertEqual(mode,'hold')

    def test_near_target_has_short_alternating_pulses_without_sleep(self):
        controller = ReelControl()
        values = [controller.decide(Tracking(350,350,35,0,0),700)[0] for _ in range(12)]
        self.assertEqual(sum(values),6)
        self.assertLessEqual(max(sum(values[i:i+3]) for i in range(10)),2)


class BiteGuardTests(unittest.TestCase):
    def test_two_fresh_frames_click_once_until_prompt_leaves(self):
        guard = BiteGuard()
        d = Detection(tap=True,scene='tap')
        self.assertFalse(guard.update(d,0))
        self.assertFalse(guard.update(d,.02))
        self.assertTrue(guard.update(d,.04))
        self.assertFalse(guard.update(d,.08))
        self.assertFalse(guard.update(d,.12))
        guard.update(Detection(track_present=True),.14)
        self.assertFalse(guard.update(d,.16))
        self.assertTrue(guard.update(d,.20))

    def test_interrupted_or_stale_evidence_cannot_confirm(self):
        guard = BiteGuard()
        d = Detection(tap=True)
        self.assertFalse(guard.update(d,0))
        self.assertFalse(guard.update(Detection(),.03))
        self.assertFalse(guard.update(d,.04))
        self.assertFalse(guard.update(d,.5))
        self.assertTrue(guard.update(d,.54))

    def test_one_frame_dropout_does_not_reclick_same_prompt(self):
        guard = BiteGuard()
        d = Detection(tap=True)
        guard.update(d,0)
        self.assertTrue(guard.update(d,.04))
        guard.update(Detection(),.06)
        self.assertFalse(guard.update(d,.08))
        self.assertFalse(guard.update(d,.12))


class NavigationTests(unittest.TestCase):
    def test_popup_stack_then_continue_and_next_round_are_not_disarmed(self):
        nav = Navigation()
        for index,scene in enumerate(('reward','item_detail','encyclopedia','action')):
            d = Detection(scene=scene,action_button=(800,650))
            start = index*2.
            self.assertIsNone(nav.update(d,start))
            self.assertEqual(nav.update(d,start+.3),(800,650))
            nav.update(Detection(),start+.4)
            nav.update(Detection(),start+.9)
            self.assertEqual(nav.confirmed,scene)
            nav.confirmed = None
        nav.update(Detection(scene='reel',track_present=True),9.)
        d = Detection(scene='action',action_button=(800,650))
        nav.update(d,10.)
        self.assertEqual(nav.update(d,10.3),(800,650))

    def test_ignored_click_retries_then_stops_instead_of_silently_waiting(self):
        nav = Navigation()
        d = Detection(scene='action',action_button=(800,650))
        nav.update(d,0)
        for i in range(6):
            self.assertEqual(nav.update(d,1.+i),(800,650))
        self.assertEqual(nav.update(d,7.),'blocked')


    def test_transient_unclicked_button_is_not_reported_as_confirmation(self):
        nav = Navigation()
        nav.update(Detection(scene='action',action_button=(800,650)),0)
        nav.update(Detection(),.1)
        nav.update(Detection(),.6)
        self.assertIsNone(nav.confirmed)

    def test_pixel_jitter_across_rounding_boundary_cannot_reset_retry_limit(self):
        nav = Navigation()
        nav.update(Detection(scene='encyclopedia',action_button=(1590,70)),0)
        for i in range(6):
            d = Detection(scene='encyclopedia',action_button=(1590+(-1)**i,70))
            self.assertIsInstance(nav.update(d,1.+i),tuple)
        self.assertEqual(nav.update(d,7.),'blocked')


class CatchLedgerTests(unittest.TestCase):
    def test_only_confirmed_card_counts_and_failure_resets_streak(self):
        ledger = CatchLedger()
        self.assertFalse(ledger.catch_seen())
        self.assertFalse(ledger.reel_started())
        self.assertTrue(ledger.catch_seen())
        self.assertFalse(ledger.catch_seen())
        self.assertEqual((ledger.catches,ledger.streak),(1,1))
        self.assertFalse(ledger.reel_started())
        self.assertTrue(ledger.reel_started())
        self.assertEqual((ledger.failed,ledger.streak),(1,0))
        self.assertTrue(ledger.catch_seen())
        self.assertEqual((ledger.rounds,ledger.catches,ledger.streak),(3,2,1))


if __name__ == '__main__':
    unittest.main()
