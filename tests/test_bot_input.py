import unittest
from unittest.mock import Mock
from bot_input import ReelActuator


class ReelActuatorTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.
        self.mouse = Mock()
        self.worker = ReelActuator(self.mouse,clock=lambda:self.now)

    def test_pulses_continue_without_new_vision_frames(self):
        self.worker.submit((100,200),'pulse',.5)
        pressed = []
        for i in range(20):
            self.now = i*.005
            self.worker.tick()
            pressed.append(self.mouse.method_calls[-1][0]=='press')
        self.assertGreaterEqual(sum(pressed),9)
        self.assertLessEqual(sum(pressed),11)
        self.assertGreaterEqual(sum(a!=b for a,b in zip(pressed,pressed[1:])),3)

    def test_stalled_vision_releases_and_cannot_resume_without_submit(self):
        self.worker.submit((100,200),'hold',.5)
        self.worker.tick()
        self.now = .151
        self.worker.tick()
        self.mouse.release.assert_called_once()
        self.mouse.reset_mock()
        self.now = .2
        self.worker.tick()
        self.mouse.press.assert_not_called()

    def test_disable_leaves_navigation_clicks_alone(self):
        self.worker.submit((100,200),'hold',.5)
        self.worker.disable()
        self.mouse.reset_mock()
        self.worker.tick()
        self.worker.close()
        self.assertEqual(self.mouse.method_calls,[])

    def test_updates_do_not_restart_the_pulse_clock(self):
        self.worker.submit((100,200),'pulse',.5)
        self.now = .035
        self.worker.submit((100,200),'pulse',.5)
        self.worker.tick()
        self.mouse.release.assert_called_once()

    def test_worker_failure_is_reported_to_runtime(self):
        self.worker.error = ValueError('mock failure')
        with self.assertRaises(RuntimeError):
            self.worker.check()
