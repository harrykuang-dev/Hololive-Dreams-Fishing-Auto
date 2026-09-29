from __future__ import annotations

import json
import math
from pathlib import Path


def rectangle(value):
    if len(value) != 4 or not all(math.isfinite(v) and 0 <= v <= 1 for v in value):
        raise ValueError("ROI must contain four finite normalized values")
    x, y, w, h = value
    if w <= 0 or h <= 0 or x + w > 1.000001 or y + h > 1.000001:
        raise ValueError("ROI must be a positive rectangle within the image")
    return tuple(value)


def point(value):
    if len(value) != 2 or not all(math.isfinite(v) and 0 < v < 1 for v in value):
        raise ValueError("Click point must lie inside the game client")
    return tuple(value)


class Profile:
    def __init__(self, data, directory=Path(".")):
        self.directory = Path(directory)
        if data.get("schema") != 1:
            raise ValueError("Unsupported profile schema")
        self.data = data
        self.reference_size = tuple(data["reference_size"])
        if (len(self.reference_size) != 2
                or any(type(v) is not int or not 64 <= v <= 16384 for v in self.reference_size)):
            raise ValueError("Invalid reference image size")
        self.gauge = rectangle(data["gauge"])
        self.axis = data["axis"]
        self.direction = data["hold_direction"]
        if self.axis not in ("x", "y") or self.direction not in (-1, 1):
            raise ValueError("axis must be x/y and hold_direction must be -1/+1")
        self.reel_point = point(data["reel_point"])
        self.bar_hsv = data["bar_hsv"]
        if len(self.bar_hsv) != 2 or any(len(v) != 3 for v in self.bar_hsv):
            raise ValueError("bar_hsv needs lower/upper HSV triples")
        lower, upper = self.bar_hsv
        if any(not 0 <= a <= b <= maximum for a, b, maximum in zip(lower, upper, (179, 255, 255))):
            raise ValueError("Invalid HSV bounds")
        self.fish_template = self.asset(data["fish_template"])
        self.fish_threshold = float(data.get("fish_threshold", .8))
        self.threshold = float(data.get("scene_threshold", .88))
        if not all(.5 <= v <= 1 for v in (self.threshold, self.fish_threshold)):
            raise ValueError("Template thresholds must be between .5 and 1")
        self.scenes = data["scenes"]
        if not {"playing", "success", "failure"} <= self.scenes.keys():
            raise ValueError("playing/success/failure scene templates are required")
        if not self.scenes.keys() <= {"ready", "waiting", "bite", "playing", "success", "failure"}:
            raise ValueError("Unknown scene name")
        for name, item in self.scenes.items():
            rectangle(item["roi"])
            self.asset(item["template"])
            if "click" in item:
                point(item["click"])
        provided_control = data.get("control", {})
        if not provided_control.keys() <= {"kp", "kd", "lead", "deadband"}:
            raise ValueError("Unknown controller parameter")
        self.control = {}
        for name, default, low, high in (("kp", 7., .1, 30.), ("kd", .65, 0., 3.),
                                        ("lead", .08, 0., .3), ("deadband", .012, 0., .1)):
            value = float(provided_control.get(name, default))
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"Invalid controller parameter {name}")
            self.control[name] = value

    def asset(self, name):
        relative = Path(name)
        result = (self.directory / relative).resolve()
        if relative.is_absolute() or not result.is_relative_to(self.directory.resolve()):
            raise ValueError("Template paths must remain inside the profile directory")
        if not result.is_file():
            raise ValueError(f"Missing template: {relative}")
        return result

    @classmethod
    def load(cls, path):
        path = Path(path)
        return cls(json.loads(path.read_text(encoding="utf-8")), path.parent)
