"""Latched, bounded bait recovery. An absent warning never clears the latch."""
from dataclasses import dataclass


@dataclass
class BaitDecision:
    managed: bool = False
    action: tuple | None = None
    failed: bool = False
    phase: str = ''
    scroll: bool = False


class BaitSwitcher:
    def __init__(self, enabled=False, result_settle=1.5, button_settle=.65):
        self.enabled = enabled
        self.result_settle = result_settle
        self.button_settle = button_settle
        self.result_since = None
        self.buttons_since = None
        self.result_absent_since = None
        self.pending_exhausted = False
        self.phase = 'idle'
        self.since = 0.
        self.stable_since = None
        self.disabled_since = None
        self.last_click = -100.
        self.attempts = 0
        self.scroll_attempts = 0
        self.probed = False
        self.retry_suspected = False
        self.latched = False

    def enter(self, phase, now):
        self.phase, self.since = phase, now
        self.stable_since = None
        self.disabled_since = None
        self.attempts = 0
        self.scroll_attempts = 0

    def stable(self, condition, now, duration=.5):
        if not condition:
            self.stable_since = None
            return False
        if self.stable_since is None:
            self.stable_since = now
        return now-self.stable_since >= duration

    def update(self, o, now, continue_attempts=0):
        if not self.enabled:
            return BaitDecision()
        if self.phase == 'idle':
            if not o.result:
                self.buttons_since = None
                if self.result_absent_since is None:
                    self.result_absent_since = now
                if now-self.result_absent_since >= .4:
                    self.result_since = self.buttons_since = None
                    self.pending_exhausted = False
                return BaitDecision()
            self.result_absent_since = None
            if self.result_since is None:
                self.result_since = now
            self.pending_exhausted |= o.exhausted
            if o.change_point and o.continue_visible:
                if self.buttons_since is None:
                    self.buttons_since = now
            else:
                self.buttons_since = None
            # GET can appear before the bottom buttons exist. A fallback
            # Continue coordinate is not evidence that input is accepted.
            if (now-self.result_since < self.result_settle or self.buttons_since is None
                    or now-self.buttons_since < self.button_settle):
                if now-self.result_since > 8.:
                    self.enter('failed',now)
                    return BaitDecision(True,failed=True,phase='failed')
                return BaitDecision(True, phase='settling')
            if o.result and (self.pending_exhausted or o.dim_continue or continue_attempts >= 2):
                self.probed = continue_attempts > 0
                self.retry_suspected = continue_attempts >= 2
                self.latched = self.pending_exhausted
                self.enter('inspect', now)
            else:
                return BaitDecision()
        if self.phase == 'failed':
            return BaitDecision(True, failed=True, phase=self.phase)
        if now-self.since > 8.:
            self.enter('failed', now)
            return BaitDecision(True, failed=True, phase=self.phase)
        decision = BaitDecision(True, phase=self.phase)
        if o.exhausted:
            self.latched = True
        if self.phase == 'inspect':
            # The warning is triggered by Continue. Probe once, then hold all
            # navigation while it settles. A prior navigation click counts.
            if not self.latched and not self.probed and o.result and o.dim_continue and o.continue_point and now-self.since >= .25:
                self.probed = True
                self.last_click = now
                self.disabled_since = None
                decision.action = o.continue_point
                return decision
            # Some depleted results have no red warning at all. A verified
            # result with a persistently disabled Continue and Change Bait
            # establishes recovery, while a brief fade only pauses input.
            if o.result and o.dim_continue and o.change_point:
                if self.disabled_since is None:
                    self.disabled_since = now
                if now-self.disabled_since >= 1.5:
                    self.latched = True
            else:
                self.disabled_since = None
            if not self.latched and self.stable(not o.result or not o.dim_continue, now, 1.5):
                # Repeated Continue clicks which did not change the scene must
                # stop, even if animation hid both warning and dim glyphs.
                if self.retry_suspected and o.result:
                    self.enter('failed', now)
                    return BaitDecision(True, failed=True, phase='failed')
                self.enter('idle', now)
                return decision
            if self.latched and now-self.since >= .65 and o.result and o.change_point:
                self.enter('opening', now)
        elif self.phase == 'opening' and o.dialog:
            self.enter('selecting', now)
        elif self.phase == 'selecting' and self.stable(o.dialog and o.selected_infinite, now):
            self.enter('confirming', now)
        elif self.phase == 'confirming' and not o.dialog:
            self.enter('returning', now)
        elif self.phase == 'returning':
            if self.stable(o.result and not o.exhausted and not o.dim_continue, now, .65):
                self.latched = False
                self.pending_exhausted = False
                self.enter('idle', now)
            return decision
        decision.phase = self.phase
        point = None
        if self.phase == 'opening' and o.result:
            point = o.change_point
        elif self.phase == 'selecting' and o.dialog and not o.selected_infinite:
            point = o.infinite_point or o.scroll_point
            decision.scroll = o.infinite_point is None and o.scroll_point is not None
        elif self.phase == 'confirming' and o.dialog and o.selected_infinite:
            point = o.confirm_point
        attempts = self.scroll_attempts if decision.scroll else self.attempts
        if point and now-self.last_click >= 1.2 and attempts < 3:
            decision.action = point
            self.last_click = now
            if decision.scroll:
                self.scroll_attempts += 1
            else:
                self.attempts += 1
        return decision
