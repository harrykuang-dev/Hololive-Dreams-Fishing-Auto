"""Temporal tracking, predictive reel control and confirmed UI retries."""
from dataclasses import dataclass
import math


@dataclass
class Tracking:
    player: float
    fish: float
    bar_height: float
    player_velocity: float
    fish_velocity: float
    predicted: bool = False


class ReelTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last = None
        self.time = None
        self.valid_time = None
        self.rejected = 0

    def update(self, d, now, height):
        if not d.track_present:
            self.reset()
            return None
        dt = now-self.time if self.time is not None else 0
        if dt < 0 or dt > .25:
            self.reset()
            dt = 0
        if d.minigame:
            p, f = d.player_center[1], d.fish_center[1]
            bh = d.player_box[3]
            vp = vf = 0.
            if self.last and dt > 0:
                old = self.last
                # A fish can hide one end of a very small bar. Retain the
                # established per-round height and choose its plausible edge.
                if bh < old.bar_height*.78 and abs(p-f)<old.bar_height:
                    top = d.player_box[1]
                    candidates = (top+old.bar_height/2,top+bh-old.bar_height/2)
                    predicted = old.player+old.player_velocity*dt
                    p = min(candidates,key=lambda value:abs(value-predicted))
                    bh = old.bar_height
                if abs(p-old.player)>2.5*height*dt+.025*height or abs(f-old.fish)>2.2*height*dt+.025*height:
                    self.rejected += 1
                    # Two implausible frames are not evidence of a new target.
                    # Sustained displacement reacquires without inherited speed.
                    if self.rejected < 3:
                        return self._coast(now,height)
                else:
                    alpha = 1-math.exp(-dt/.065)
                    vp = old.player_velocity*(1-alpha)+(p-old.player)/dt*alpha
                    vf = old.fish_velocity*(1-alpha)+(f-old.fish)/dt*alpha
                    vp = max(-2.5*height,min(2.5*height,vp))
                    vf = max(-2.2*height,min(2.2*height,vf))
                    bh = old.bar_height*.85+bh*.15
            self.last = Tracking(p,f,bh,vp,vf)
            self.time = self.valid_time = now
            self.rejected = 0
            return self.last
        return self._coast(now,height)

    def _coast(self, now, height):
        if self.last is None or now-self.valid_time>.14:
            return None
        dt = max(0,min(.14,now-self.time))
        old = self.last
        # Predict a brief sprite occlusion, but do not integrate it forever.
        return Tracking(max(0,min(height,old.player+old.player_velocity*dt)),
                        max(0,min(height,old.fish+old.fish_velocity*dt)),
                        old.bar_height,old.player_velocity,old.fish_velocity,True)


class ReelControl:
    def __init__(self, lead=.20):
        self.lead = lead
        self.accumulator = 0.

    def reset(self):
        self.accumulator = 0.

    def decide(self, t, height):
        # Shorter horizon for agile fish: their next reversal is uncertain.
        fish_lead = min(.08,self.lead*.65)
        error = t.player+t.player_velocity*self.lead-(t.fish+t.fish_velocity*fish_lead)
        band = max(3.,t.bar_height*.22)
        if error > band:
            return True,'hold',error
        if error < -band:
            return False,'release',error
        # Pulse-density modulation is non-blocking: close to the fish the
        # button alternates rapidly, with duty adjusted to its speed/error.
        duty = max(.18,min(.82,.50+.28*error/band-.12*t.fish_velocity/height))
        self.accumulator += duty
        pressed = self.accumulator >= 1.
        if pressed:
            self.accumulator -= 1.
        return pressed,'pulse',error


class Navigation:
    """Cross-frame debounce + bounded retries; never permanently disarm."""
    def __init__(self):
        self.key = None
        self.since = 0.
        self.last_click = -100.
        self.attempts = 0
        self.absent_since = None
        self.confirmed = None

    def update(self, d, now):
        if not d.action_button:
            if self.absent_since is None:
                self.absent_since = now
            if self.key is not None and now-self.absent_since>.4:
                if self.attempts:
                    self.confirmed = self.key[0]
                self.key = None
                self.attempts = 0
            return None
        self.absent_since = None
        point = d.action_button
        key = (d.scene,point[0],point[1])
        changed = self.key is None or d.scene != self.key[0] or math.hypot(point[0]-self.key[1],point[1]-self.key[2])>20
        if changed:
            if self.key is not None and self.attempts:
                self.confirmed = self.key[0]
            self.key,self.since,self.attempts = key,now,0
        # Animation can expose a button before it accepts input.
        if now-self.since<.22 or now-self.last_click<.85:
            return None
        if self.attempts>=6:
            return 'blocked'
        self.last_click = now
        self.attempts += 1
        return point
