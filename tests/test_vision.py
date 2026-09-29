import copy
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from fishing_auto.profile import Profile
from fishing_auto.vision import Vision, save_image


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        rng = np.random.default_rng(541)
        self.fish = rng.integers(40, 240, (8, 10, 3), dtype=np.uint8)
        save_image(self.directory / "fish.png", self.fish)
        self.scenes = {}
        self.frames = {}
        for name in ("playing", "success", "failure"):
            image = np.zeros((400, 400, 3), dtype=np.uint8)
            marker = rng.integers(0, 255, (30, 50, 3), dtype=np.uint8)
            image[20:50, 20:70] = marker
            save_image(self.directory / f"{name}.png", marker)
            self.frames[name] = image
            self.scenes[name] = {"roi": [.05, .05, .125, .075], "template": f"{name}.png"}
        playing = self.frames["playing"]
        playing[174:198, 160:210] = (0, 230, 0)
        playing[161:169, 180:190] = self.fish
        self.data = {"schema": 1, "reference_size": [400, 400], "axis": "x",
                     "hold_direction": 1, "reel_point": [.8, .8],
                     "gauge": [.2, .4, .6, .1], "bar_hsv": [[45, 120, 120], [85, 255, 255]],
                     "fish_template": "fish.png", "scenes": self.scenes}
        self.profile = Profile(self.data, self.directory)
        self.vision = Vision(self.profile)

    def tearDown(self):
        self.temp.cleanup()

    def test_recognizes_distinct_scenes_and_tracks_horizontal_gauge(self):
        for name, frame in self.frames.items():
            observation = self.vision.observe(frame)
            self.assertEqual(observation.scene, name)
            if name == "playing":
                self.assertIsNotNone(observation.tracking)
                self.assertAlmostEqual(observation.tracking.fish, 105 / 240)
                self.assertAlmostEqual(observation.tracking.bar, 105 / 240)
                self.assertAlmostEqual(observation.tracking.width, 50 / 240)
            else:
                self.assertIsNone(observation.tracking)

    def test_missing_fish_is_rejected(self):
        frame = self.frames["playing"].copy()
        frame[161:169, 180:190] = 0
        self.assertIsNone(self.vision.observe(frame).tracking)

    def test_two_matching_fish_icons_are_rejected(self):
        frame = self.frames["playing"].copy()
        frame[161:169, 260:270] = self.fish
        self.assertIsNone(self.vision.observe(frame).tracking)

    def test_two_bars_are_rejected(self):
        frame = self.frames["playing"].copy()
        frame[174:198, 240:290] = (0, 230, 0)
        self.assertIsNone(self.vision.observe(frame).tracking)

    def test_background_and_blank_screens_do_not_become_success(self):
        observation = self.vision.observe(np.zeros((400, 400, 3), dtype=np.uint8))
        self.assertEqual(observation.scene, "unknown")
        self.assertIsNone(observation.tracking)

    def test_ambiguous_scene_is_rejected(self):
        save_image(self.directory / "success.png", self.frames["playing"][20:50, 20:70])
        vision = Vision(self.profile)
        self.assertEqual(vision.observe(self.frames["playing"]).scene, "unknown")

    def test_aspect_ratio_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "aspect ratio"):
            self.vision.observe(np.zeros((200, 400, 3), dtype=np.uint8))

    def test_vertical_gauge(self):
        data = copy.deepcopy(self.data)
        data["axis"] = "y"
        data["gauge"] = [.2, .4, .1, .6]
        frame = self.frames["playing"].copy()
        frame[160:200, 80:320] = 0
        frame[240:290, 94:118] = (0, 230, 0)
        frame[260:268, 81:91] = self.fish
        track = Vision(Profile(data, self.directory)).observe(frame).tracking
        self.assertIsNotNone(track)
        self.assertAlmostEqual(track.fish, 104 / 240)
        self.assertAlmostEqual(track.bar, 105 / 240)

    def test_template_paths_cannot_escape_profile(self):
        data = copy.deepcopy(self.data)
        data["fish_template"] = "../outside.png"
        with self.assertRaisesRegex(ValueError, "inside"):
            Profile(data, self.directory)

    def test_out_of_bounds_or_nan_coordinates_are_rejected(self):
        for value in ([.8, .4, .6, .1], [float("nan"), .4, .6, .1]):
            data = copy.deepcopy(self.data)
            data["gauge"] = value
            with self.assertRaises(ValueError):
                Profile(data, self.directory)

    def test_numeric_control_parameters_are_normalized(self):
        data = copy.deepcopy(self.data)
        data["control"] = {"kp": "7", "lead": ".08"}
        profile = Profile(data, self.directory)
        self.assertEqual(profile.control["kp"], 7.)
        self.assertIsInstance(profile.control["lead"], float)

    def test_unknown_control_parameter_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["control"] = {"bad": 7.}
        with self.assertRaisesRegex(ValueError, "Unknown controller"):
            Profile(data, self.directory)


if __name__ == "__main__":
    unittest.main()
