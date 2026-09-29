from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .control import Tracking


def read_image(path):
    data = np.fromfile(Path(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot decode image: {path}")
    return image


def save_image(path, image):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, data = cv2.imencode(".png", image)
    if not ok:
        raise OSError("PNG encoding failed")
    data.tofile(path)


def crop(image, rect):
    height, width = image.shape[:2]
    x, y, w, h = rect
    x0, y0 = round(x * width), round(y * height)
    x1, y1 = round((x + w) * width), round((y + h) * height)
    region = image[y0:y1, x0:x1]
    if region.size == 0:
        raise ValueError("Empty ROI")
    return region


def correlation(image, template):
    if image.shape != template.shape or min(template.shape[:2]) < 3:
        return 0.
    if float(template.std()) < 8:
        return 0.  # Flat background is not a scene identity.
    score = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)[0, 0]
    return float(score) if np.isfinite(score) else 0.


@dataclass(frozen=True)
class Observation:
    scene: str
    scores: dict
    tracking: Tracking | None


class Vision:
    def __init__(self, profile):
        self.profile = profile
        self.templates = {name: cv2.cvtColor(read_image(profile.asset(item["template"])),
                                             cv2.COLOR_BGR2GRAY)
                          for name, item in profile.scenes.items()}
        self.fish = cv2.cvtColor(read_image(profile.fish_template), cv2.COLOR_BGR2GRAY)
        if float(self.fish.std()) < 8:
            raise ValueError("Fish template is flat; select the fish icon tightly")

    def observe(self, frame):
        width, height = self.profile.reference_size
        fh, fw = frame.shape[:2]
        if abs((fw / fh) / (width / height) - 1) > .01:
            raise ValueError("Game aspect ratio differs from calibration")
        if (fw, fh) != (width, height):
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        scores = {}
        for name, item in self.profile.scenes.items():
            region = cv2.cvtColor(crop(frame, item["roi"]), cv2.COLOR_BGR2GRAY)
            scores[name] = correlation(region, self.templates[name])
        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        scene = "unknown"
        if ranked[0][1] >= self.profile.threshold and ranked[0][1] - ranked[1][1] >= .06:
            scene = ranked[0][0]
        tracking = self.track(crop(frame, self.profile.gauge)) if scene == "playing" else None
        return Observation(scene, scores, tracking)

    def track(self, gauge):
        hsv = cv2.cvtColor(gauge, cv2.COLOR_BGR2HSV)
        lower, upper = (np.asarray(v, dtype=np.uint8) for v in self.profile.bar_hsv)
        mask = cv2.inRange(hsv, lower, upper)
        axis = 0 if self.profile.axis == "x" else 1
        cross = mask.shape[axis]
        # Cross-axis occupancy survives a fish drawn over the colored bar.
        occupied = np.count_nonzero(mask, axis=axis) >= max(2, round(cross * .28))
        runs = []
        begin = None
        for i, present in enumerate(np.r_[occupied, False]):
            if present and begin is None:
                begin = i
            elif not present and begin is not None:
                runs.append((begin, i))
                begin = None
        # Fill very small holes, but never merge separate distant candidates.
        merged = []
        for a, b in runs:
            if merged and a - merged[-1][1] <= 2:
                merged[-1] = (merged[-1][0], b)
            else:
                merged.append((a, b))
        length = len(occupied)
        candidates = [(a, b) for a, b in merged if .025 <= (b - a) / length <= .65]
        if len(candidates) != 1:
            return None
        a, b = candidates[0]
        gray = cv2.cvtColor(gauge, cv2.COLOR_BGR2GRAY)
        th, tw = self.fish.shape
        if th > gray.shape[0] or tw > gray.shape[1]:
            return None
        matches = cv2.matchTemplate(gray, self.fish, cv2.TM_CCOEFF_NORMED)
        _, peak, _, location = cv2.minMaxLoc(matches)
        if not np.isfinite(peak) or peak < self.profile.fish_threshold:
            return None
        alternatives = matches.copy()
        px, py = location
        alternatives[max(0, py - th // 2):py + th // 2 + 1,
                     max(0, px - tw // 2):px + tw // 2 + 1] = -1
        if float(alternatives.max()) > peak - .06:
            return None  # Ambiguous fish icon: release instead of guessing.
        fish_position = ((px + tw / 2) if self.profile.axis == "x" else (py + th / 2)) / length
        return Tracking(fish_position, (a + b) / (2 * length), (b - a) / length, float(peak))
