"""Independent reel pulse clock; no capture, vision, or Windows dependencies."""
import threading
import time


class ReelActuator:
    """Keep short pulses independent of image processing and PNG writes.

    The runtime must disable this worker before any navigation click. A
    watchdog releases input if fresh tracking commands stop arriving.
    """
    def __init__(self, mouse, period=.05, watchdog=.15, clock=time.perf_counter):
        self.mouse = mouse
        self.period = period
        self.watchdog = watchdog
        self.clock = clock
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.command = None
        self.error = None
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run,daemon=True,name='reel-pulses')
        self.thread.start()

    def submit(self, point, mode, duty):
        with self.lock:
            now = self.clock()
            origin = self.command[4] if self.command else now
            self.command = (point,mode,max(.1,min(.9,duty)),now,origin)

    def disable(self):
        with self.lock:
            if self.command is not None:
                self.command = None
                self.mouse.release()

    def check(self):
        if self.error is not None:
            raise RuntimeError('Reel input worker failed') from self.error

    def tick(self):
        with self.lock:
            if self.command is None:
                return
            point,mode,duty,updated,origin = self.command
            now = self.clock()
            if now < updated or now-updated > self.watchdog:
                self.command = None
                self.mouse.release()
                return
            pressed = mode == 'hold' or (mode == 'pulse' and (now-origin)%self.period < self.period*duty)
            if pressed:
                self.mouse.press(point)
            else:
                self.mouse.release()

    def _run(self):
        try:
            while not self.stop_event.is_set():
                self.tick()
                self.stop_event.wait(.005)
        except Exception as exc:
            self.error = exc
            self.disable()

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=.5)
        self.disable()
