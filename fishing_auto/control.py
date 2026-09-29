from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Tracking:
    fish: float
    bar: float
    width: float
    confidence: float = 1.

    def valid(self):
        return (all(math.isfinite(v) for v in (self.fish, self.bar, self.width, self.confidence))
                and 0 <= self.fish <= 1 and 0 <= self.bar <= 1
                and 0 < self.width < .9 and .5 <= self.confidence <= 1)


class Controller:
    """Velocity-damped follower; screen position and time are the only inputs.

    Coordinates increase rightward/downward. direction specifies the movement
    caused by holding the reel. Parameters need validation against real footage.
    """
    def __init__(self, direction=1, kp=7., kd=.65, lead=.08, deadband=.012):
        if direction not in (-1, 1):
            raise ValueError("direction must be -1/+1")
        self.direction = direction
        self.kp, self.kd, self.lead, self.deadband = kp, kd, lead, deadband
        self.reset()

    def reset(self):
        self.previous = None
        self.fish_velocity = self.bar_velocity = 0.
        self.holding = False

    def update(self, t, track):
        if not math.isfinite(t) or track is None or not track.valid():
            self.reset()
            return False
        if self.previous is None:
            self.previous = (t, track)
            return False  # First frame establishes a velocity baseline.
        old_t, old = self.previous
        dt = t - old_t
        if dt <= 0 or dt > .2:
            self.reset()
            self.previous = (t, track)
            return False
        alpha = 1 - math.exp(-dt / .06)
        limit = 3.
        fish_v = max(-limit, min(limit, (track.fish - old.fish) / dt))
        bar_v = max(-limit, min(limit, (track.bar - old.bar) / dt))
        self.fish_velocity += alpha * (fish_v - self.fish_velocity)
        self.bar_velocity += alpha * (bar_v - self.bar_velocity)
        predicted_fish = max(track.width / 2, min(1 - track.width / 2,
                                                track.fish + self.lead * self.fish_velocity))
        error = predicted_fish - track.bar
        signal = self.direction * (self.kp * error
                                  + self.kd * (self.fish_velocity - self.bar_velocity))
        band = self.kp * self.deadband
        if signal > band:
            self.holding = True
        elif signal < -band:
            self.holding = False
        self.previous = (t, track)
        return self.holding
