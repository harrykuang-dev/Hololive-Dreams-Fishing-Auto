from __future__ import annotations

from dataclasses import dataclass

from .control import Controller


@dataclass(frozen=True)
class Decision:
    hold: bool = False
    click: str | None = None
    event: str | None = None
    stop: str | None = None


class Engine:
    """Bounded rounds with positive result evidence and one-shot menu input."""
    def __init__(self, controller=None, rounds=1, auto_cycle=False,
                 unknown_timeout=2., round_timeout=90.):
        if not 1 <= rounds <= 100:
            raise ValueError("rounds must be between 1 and 100")
        self.controller = controller or Controller()
        self.rounds, self.auto_cycle = rounds, auto_cycle
        self.unknown_timeout, self.round_timeout = unknown_timeout, round_timeout
        self.phase = "idle"
        self.candidate = None
        self.candidate_since = None
        self.candidate_count = 0
        self.last_time = None
        self.last_seen = None
        self.started = None
        self.phase_since = None
        self.lost_since = None
        self.successes = self.failures = self.attempts = 0
        self.done = False

    def _stop(self, reason, event=None):
        self.controller.reset()
        self.done = True
        return Decision(event=event, stop=reason)

    def step(self, now, observation):
        if self.done:
            return Decision(stop="already_stopped")
        if self.last_time is not None and (now <= self.last_time or now - self.last_time > .2):
            return self._stop("invalid_or_stale_frame_time")
        self.last_time = now
        if self.started is None:
            self.started = self.last_seen = now
        scene = observation.scene
        if scene != self.candidate:
            self.candidate = scene
            self.candidate_since = now
            self.candidate_count = 1
        else:
            self.candidate_count += 1
        stable = self.candidate_count >= 2 and now - self.candidate_since >= .02
        if scene != "unknown":
            self.last_seen = now
        elif now - self.last_seen > self.unknown_timeout:
            return self._stop("unknown_screen")
        if now - self.started > self.round_timeout:
            return self._stop("round_timeout")
        if self.phase in ("idle", "between") and stable and scene == "ready":
            if self.auto_cycle:
                self.phase = "casting"
                self.phase_since = now
                self.started = now
                self.attempts += 1
                return Decision(click="ready", event="cast")
            return Decision()
        if self.phase == "casting" and stable and scene == "bite":
            self.phase = "hooking"
            self.phase_since = now
            return Decision(click="bite", event="hook")
        if self.phase in ("casting", "hooking") and now - self.phase_since > 30:
            return self._stop("cast_or_hook_timeout")
        if stable and scene == "playing" and self.phase in ("idle", "casting", "hooking", "between"):
            if self.phase in ("idle", "between"):
                self.attempts += 1
                self.started = now
            self.phase = "playing"
            self.controller.reset()
        # A result releases the reel immediately, before its confirmation.
        if scene in ("success", "failure"):
            self.controller.reset()
            self.lost_since = None
            result_allowed = (self.phase == "playing"
                              or (scene == "failure" and self.phase in ("casting", "hooking")))
            if stable and result_allowed:
                if scene == "success":
                    self.successes += 1
                else:
                    self.failures += 1
                self.phase = "result"
                if self.successes + self.failures >= self.rounds or not self.auto_cycle:
                    return self._stop("rounds_complete", event=scene)
                return Decision(click=scene, event=scene)
            return Decision()
        if self.phase == "result":
            if stable and scene == "ready":
                self.phase = "between"
                self.started = now
            return Decision()
        if (self.phase == "playing" and scene == "playing"
                and observation.tracking is not None and observation.tracking.valid()):
            self.lost_since = None
            return Decision(hold=self.controller.update(now, observation.tracking))
        if self.phase == "playing":
            self.controller.reset()
            if self.lost_since is None:
                self.lost_since = now
            elif now - self.lost_since > .25:
                return self._stop("tracking_lost")
        return Decision()

    def summary(self):
        completed = self.successes + self.failures
        return {"attempts": self.attempts, "successes": self.successes, "failures": self.failures,
                "unconfirmed": self.attempts - completed,
                "confirmed_success_rate": self.successes / completed if completed else None,
                "attempt_success_rate": self.successes / self.attempts if self.attempts else None}
