"""Synthetic motion benchmark. NEVER reports real-game catches."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fishing_auto.control import Controller, Tracking


def trial(seed, parameters):
    rng = random.Random(seed)
    control = Controller(**parameters)
    position, velocity, t = .5, 0., 0.
    width = rng.uniform(.15, .28)
    frequency = rng.uniform(.12, .4)
    phase = rng.uniform(0, math.pi)
    target, fish, next_change = .5, .5, 0.
    overlap = samples = 0
    error_sum = 0.
    for _ in range(900):
        dt = rng.uniform(1 / 60, 1 / 30)
        t += dt
        if t >= next_change:
            target = rng.uniform(.1, .9)
            next_change = t + rng.uniform(.6, 2.5)
        baseline = .5 + .20 * math.sin(frequency * t + phase) + .08 * math.sin(1.8 * t)
        fish += max(-.7 * dt, min(.7 * dt, .6 * target + .4 * baseline - fish))
        holding = control.update(t, Tracking(fish, position, width))
        acceleration = (1.8 if holding else -1.8) - 4 * velocity
        velocity = max(-.55, min(.55, velocity + acceleration * dt))
        position = max(width / 2, min(1 - width / 2, position + velocity * dt))
        if position in (width / 2, 1 - width / 2):
            velocity = 0.
        if t > 2:
            overlap += abs(fish - position) <= width / 2
            error_sum += abs(fish - position)
            samples += 1
    return {"overlap_fraction": overlap / samples, "mean_position_error": error_sum / samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    args = parser.parse_args()
    candidates = [{"kp": kp, "kd": kd, "lead": lead, "deadband": .012}
                  for kp in (4., 7., 10.) for kd in (.4, .65, .9) for lead in (.04, .08, .12)]
    train = []
    for parameters in candidates:
        runs = [trial(seed, parameters) for seed in range(12)]
        train.append((sum(run["overlap_fraction"] for run in runs) / len(runs), parameters))
    score, best = max(train, key=lambda pair: pair[0])
    heldout = [trial(seed, best) for seed in range(100, 150)]
    report = {"mode": "synthetic_benchmark", "live_rounds": 0, "live_success_claim": False,
              "parameters": best, "training_overlap_mean": score, "heldout_tracks": len(heldout),
              "heldout_overlap_mean": sum(run["overlap_fraction"] for run in heldout) / len(heldout),
              "heldout_overlap_min": min(run["overlap_fraction"] for run in heldout),
              "note": "Artificial physics; does not validate the game's rules, latency, colors, or success rate."}
    print(json.dumps(report, indent=2))
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as output:
            output.write(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
