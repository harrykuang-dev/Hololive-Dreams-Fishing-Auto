"""Human-operated calibration from local game-client PNGs, never guesses UI."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .profile import Profile
from .vision import Vision, read_image, save_image


def select(image, prompt):
    print(prompt, flush=True)
    rect = cv2.selectROI("Calibration: drag a rectangle, Enter accepts, Esc cancels", image,
                         showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()
    x, y, w, h = rect
    if min(w, h) < 3:
        raise ValueError("Selection cancelled or too small")
    height, width = image.shape[:2]
    return [x / width, y / height, w / width, h / height], image[y:y+h, x:x+w].copy()


def select_point(image, prompt):
    roi, _ = select(image, prompt + " (select a small box; its center will be clicked)")
    x, y, w, h = roi
    return [x + w / 2, y + h / 2]


def calibrate(args):
    destination = Path(args.output)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Output directory must be new/empty; existing profiles are preserved")
    frames = {name: read_image(getattr(args, name)) for name in
              ("playing", "success", "failure", "ready", "waiting", "bite")
              if getattr(args, name, None)}
    playing = frames["playing"]
    height, width = playing.shape[:2]
    if any(frame.shape != playing.shape for frame in frames.values()):
        raise ValueError("All calibration images must have the same game-client dimensions")
    print("Use images of this game's fishing UI only. No example color/coordinates are supplied.")
    gauge_roi, gauge = select(playing, "1. Select the complete fish movement gauge (exclude other HUD).")
    fish_roi, fish = select(playing, "2. Tightly select the moving fish icon, including distinctive details.")
    if float(cv2.cvtColor(fish, cv2.COLOR_BGR2GRAY).std()) < 8:
        raise ValueError("Fish template is flat")
    gx, gy, gw, gh = gauge_roi
    fx, fy, fw, fh = fish_roi
    if not (gx <= fx and gy <= fy and fx + fw <= gx + gw and fy + fh <= gy + gh):
        raise ValueError("Fish template must be contained in the gauge")
    _, sample = select(playing, "3. Select ONLY the solid colored interior of the player-controlled bar.")
    hsv = cv2.cvtColor(sample, cv2.COLOR_BGR2HSV)
    median = np.median(hsv.reshape(-1, 3), axis=0)
    if median[1] < 45:
        raise ValueError("Bar sample has too little saturation; select its colored interior")
    bounds = [np.maximum([0, 25, 25], median - [8, 65, 65]).astype(int).tolist(),
              np.minimum([179, 255, 255], median + [8, 65, 65]).astype(int).tolist()]
    reel_point = select_point(playing, "4. Select the reel control to hold during fishing.")
    scene_data, assets = {}, {"fish.png": fish}
    for name, frame in frames.items():
        roi, template = select(frame, f"Select a static marker UNIQUE to {name.upper()} (no changing numbers).")
        if float(cv2.cvtColor(template, cv2.COLOR_BGR2GRAY).std()) < 8:
            raise ValueError(f"{name} marker is flat")
        item = {"roi": roi, "template": f"{name}.png"}
        if args.auto_cycle and name in ("ready", "bite", "success", "failure"):
            item["click"] = select_point(frame, f"Select the action button for {name.upper()}.")
        scene_data[name] = item
        assets[f"{name}.png"] = template
    if args.auto_cycle and not {"ready", "waiting", "bite"} <= frames.keys():
        raise ValueError("Auto-cycle calibration also needs ready/waiting/bite images")
    destination.mkdir(parents=True, exist_ok=True)
    for name, image in assets.items():
        save_image(destination / name, image)
    data = {"schema": 1, "reference_size": [width, height], "axis": args.axis,
            "hold_direction": args.direction, "gauge": gauge_roi, "reel_point": reel_point,
            "bar_hsv": bounds, "fish_template": "fish.png", "scenes": scene_data,
            "fish_threshold": .8, "scene_threshold": .88,
            "control": {"kp": 7., "kd": .65, "lead": .08, "deadband": .012},
            "status": "human_calibrated_not_live_validated"}
    profile = Profile(data, destination)
    vision = Vision(profile)
    for name, frame in frames.items():
        observation = vision.observe(frame)
        if observation.scene != name:
            raise ValueError(f"{name} marker is ambiguous: {observation.scores}; select more distinctive markers")
        if name == "playing" and observation.tracking is None:
            raise ValueError("Cannot recognize bar/fish in calibration frame; select tighter samples")
    # Only write a runnable profile after every source frame passes recognition.
    output = destination / "profile.json"
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Profile created: {output.resolve()}\nCalibration is not a successful live fishing test.")
