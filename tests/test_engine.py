import unittest

from fishing_auto.control import Controller, Tracking
from fishing_auto.engine import Engine
from fishing_auto.vision import Observation


def observation(scene, tracking=None):
    return Observation(scene, {}, tracking)


class EngineTests(unittest.TestCase):
    def start(self, engine):
        track = Tracking(.7, .3, .2)
        engine.step(0., observation("playing", track))
        engine.step(.04, observation("playing", track))
        return engine.step(.08, observation("playing", track))

    def test_positive_success_evidence_and_no_duplicate_counting(self):
        engine = Engine()
        self.start(engine)
        first = engine.step(.12, observation("success"))
        self.assertFalse(first.hold)
        self.assertIsNone(first.event)
        confirmed = engine.step(.16, observation("success"))
        self.assertEqual(confirmed.event, "success")
        self.assertEqual(confirmed.stop, "rounds_complete")
        for t in (.20, .24, .28):
            self.assertFalse(engine.step(t, observation("success")).hold)
        self.assertEqual(engine.successes, 1)

    def test_missing_hud_is_not_a_success(self):
        engine = Engine()
        self.start(engine)
        result = None
        for i in range(1, 12):
            result = engine.step(.08 + i * .04, observation("unknown"))
            self.assertFalse(result.hold)
            if result.stop:
                break
        self.assertEqual(result.stop, "tracking_lost")
        self.assertEqual(engine.summary()["unconfirmed"], 1)
        self.assertEqual(engine.successes, 0)

    def test_tracking_loss_immediately_releases(self):
        engine = Engine()
        self.assertTrue(self.start(engine).hold)
        self.assertFalse(engine.step(.12, observation("playing", None)).hold)

    def test_stale_time_stops_with_unconfirmed_attempt(self):
        engine = Engine()
        self.start(engine)
        self.assertEqual(engine.step(.4, observation("playing", Tracking(.7, .3, .2))).stop,
                         "invalid_or_stale_frame_time")
        self.assertEqual(engine.summary()["attempt_success_rate"], 0.)

    def test_time_reversal_stops(self):
        engine = Engine()
        self.start(engine)
        self.assertEqual(engine.step(.07, observation("success")).stop,
                         "invalid_or_stale_frame_time")

    def test_unknown_startup_times_out_without_clicking(self):
        engine = Engine(unknown_timeout=.12)
        for t in (0., .04, .08, .12, .16):
            result = engine.step(t, observation("unknown"))
            self.assertIsNone(result.click)
        self.assertEqual(result.stop, "unknown_screen")
        self.assertEqual(engine.attempts, 0)

    def test_round_timeout(self):
        engine = Engine(round_timeout=.16)
        self.start(engine)
        engine.step(.12, observation("playing", Tracking(.7, .3, .2)))
        engine.step(.16, observation("playing", Tracking(.7, .3, .2)))
        self.assertEqual(engine.step(.24, observation("playing", Tracking(.7, .3, .2))).stop,
                         "round_timeout")

    def test_two_rounds_one_shot_cast_hook_ack_and_results(self):
        engine = Engine(rounds=2, auto_cycle=True)
        timeline = ["ready"] * 4 + ["waiting"] * 3 + ["bite"] * 4 + ["playing"] * 4
        timeline += ["success"] * 4 + ["ready"] * 5 + ["waiting"] * 3
        timeline += ["bite"] * 4 + ["playing"] * 4 + ["failure"] * 4
        clicks = []
        events = []
        for i, scene in enumerate(timeline):
            result = engine.step(i * .04, observation(scene, Tracking(.6, .4, .2)
                                                       if scene == "playing" else None))
            if result.click:
                clicks.append(result.click)
            if result.event:
                events.append(result.event)
            if result.stop:
                break
        self.assertEqual(clicks, ["ready", "bite", "success", "ready", "bite"])
        self.assertEqual(events, ["cast", "hook", "success", "cast", "hook", "failure"])
        self.assertEqual(engine.summary()["attempts"], 2)
        self.assertEqual(engine.summary()["unconfirmed"], 0)
        self.assertEqual(engine.summary()["confirmed_success_rate"], .5)

    def test_result_at_start_does_not_count_previous_round(self):
        engine = Engine()
        for t in (0., .04, .08):
            engine.step(t, observation("success"))
        self.assertEqual(engine.successes, 0)

    def test_casting_cannot_count_success_without_gameplay(self):
        engine = Engine(auto_cycle=True)
        for i, scene in enumerate(["ready", "ready", "success", "success", "success"]):
            result = engine.step(i * .04, observation(scene))
        self.assertEqual(engine.successes, 0)
        self.assertIsNone(result.event)

    def test_invalid_tracking_cannot_reset_loss_timeout(self):
        engine = Engine()
        self.start(engine)
        for i in range(1, 12):
            result = engine.step(.08 + i * .04, observation("playing", Tracking(.5, .5, 0.)))
            if result.stop:
                break
        self.assertEqual(result.stop, "tracking_lost")


class ControllerTests(unittest.TestCase):
    def test_invalid_or_lost_tracking_releases_and_clears_velocity(self):
        control = Controller()
        control.update(0., Tracking(.8, .2, .2))
        self.assertTrue(control.update(.04, Tracking(.8, .2, .2)))
        for track in (None, Tracking(float("nan"), .2, .2), Tracking(.5, .5, 0.)):
            self.assertFalse(control.update(.08, track))
            self.assertIsNone(control.previous)

    def test_horizontal_and_inverted_vertical_direction(self):
        for direction, expected in ((1, True), (-1, False)):
            control = Controller(direction)
            self.assertFalse(control.update(0., Tracking(.8, .2, .2)))
            self.assertEqual(control.update(.04, Tracking(.8, .2, .2)), expected)

    def test_large_frame_gap_clears_momentum(self):
        control = Controller()
        control.update(0., Tracking(.8, .2, .2))
        control.update(.04, Tracking(.8, .2, .2))
        self.assertFalse(control.update(1., Tracking(.8, .2, .2)))


if __name__ == "__main__":
    unittest.main()
