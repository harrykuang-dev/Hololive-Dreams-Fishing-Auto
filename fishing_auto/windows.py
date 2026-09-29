"""Windows runtime for the user-run bot; not used by offline tests."""
from __future__ import annotations

import ctypes
from pathlib import Path
import time

import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui


class GameWindow:
    def __init__(self, title="hololive-Dreams"):
        ctypes.windll.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
        candidates = []
        def visit(hwnd, _):
            if (win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == title
                    and win32gui.GetClassName(hwnd) == "UnityWndClass"):
                candidates.append(hwnd)
        win32gui.EnumWindows(visit, None)
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one game window titled {title!r}; found {len(candidates)}")
        self.hwnd = candidates[0]
        self.holding = False
        self.geometry = None
        self._closed = False

    @staticmethod
    def stop_pressed():
        return bool(win32api.GetAsyncKeyState(win32con.VK_F9) & 0x8000)

    def check(self):
        if self.stop_pressed():
            raise RuntimeError("F9 stop requested")
        if (not win32gui.IsWindow(self.hwnd) or win32gui.IsIconic(self.hwnd)
                or win32gui.GetForegroundWindow() != self.hwnd):
            raise RuntimeError("Game must remain in the foreground and not minimized")
        _, _, width, height = win32gui.GetClientRect(self.hwnd)
        x, y = win32gui.ClientToScreen(self.hwnd, (0, 0))
        user = ctypes.windll.user32
        vx, vy = user.GetSystemMetrics(76), user.GetSystemMetrics(77)
        vw, vh = user.GetSystemMetrics(78), user.GetSystemMetrics(79)
        if (width < 64 or height < 64 or x < vx or y < vy
                or x + width > vx + vw or y + height > vy + vh):
            raise RuntimeError("Game client is not entirely on screen")
        geometry = (x, y, width, height)
        if self.geometry is None:
            self.geometry = geometry
        elif geometry != self.geometry:
            raise RuntimeError("Window moved/resized during the session")
        above = win32gui.GetWindow(self.hwnd, win32con.GW_HWNDPREV)
        visited = set()
        while above:
            if above in visited:
                raise RuntimeError("Window order changed during visibility check")
            visited.add(above)
            if win32gui.IsWindowVisible(above) and not win32gui.IsIconic(above):
                cloaked = ctypes.c_int()
                status = ctypes.windll.dwmapi.DwmGetWindowAttribute(
                    ctypes.c_void_p(above), 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
                if status != 0 or not cloaked.value:
                    left, top, right, bottom = win32gui.GetWindowRect(above)
                    if max(left, x) < min(right, x + width) and max(top, y) < min(bottom, y + height):
                        raise RuntimeError("Another window overlays the game")
            above = win32gui.GetWindow(above, win32con.GW_HWNDPREV)
        return geometry

    def capture(self):
        x, y, width, height = self.check()
        dc = win32gui.GetDC(0)
        source = win32ui.CreateDCFromHandle(dc)
        memory = source.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        previous = None
        try:
            bitmap.CreateCompatibleBitmap(source, width, height)
            previous = memory.SelectObject(bitmap)
            memory.BitBlt((0, 0), (width, height), source, (x, y), win32con.SRCCOPY)
            frame = np.frombuffer(bitmap.GetBitmapBits(True), dtype=np.uint8)
            frame = frame.reshape(height, width, 4)[:, :, :3].copy()
            self.check()
            return frame
        finally:
            if previous is not None:
                memory.SelectObject(previous)
            win32gui.DeleteObject(bitmap.GetHandle())
            memory.DeleteDC()
            win32gui.ReleaseDC(0, dc)

    def hold(self, down, position):
        if down:
            self.check()
        if down == self.holding:
            return
        if down:
            x, y, width, height = self.check()
            px, py = x + round(position[0] * width), y + round(position[1] * height)
            if win32gui.GetAncestor(win32gui.WindowFromPoint((px, py)), win32con.GA_ROOT) != self.hwnd:
                raise RuntimeError("Reel point is outside the target window")
            win32api.SetCursorPos((px, py))
            self.check()
            # Track ownership before injection so error paths also release it.
            self.holding = True
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        else:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            self.holding = False

    def click(self, position):
        self.hold(False, position)
        try:
            self.hold(True, position)
            time.sleep(.025)
        finally:
            self.hold(False, position)

    def close(self):
        if not self._closed:
            self.hold(False, (.5, .5))
            self._closed = True


class VideoRecorder:
    """Lossless ordered frame mapping; no fictitious achieved FPS claim.

    MP4 uses the requested nominal FPS. Actual capture times live in JSONL.
    Encoding runs synchronously; the loop rejects excessive latency.
    """
    def __init__(self, path, size, fps):
        self.writer = cv2.VideoWriter(str(Path(path)), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
        if not self.writer.isOpened():
            self.writer.release()
            raise OSError("Cannot open recording encoder")
        self.frames = 0

    def write(self, frame):
        self.writer.write(frame)
        self.frames += 1

    def close(self):
        self.writer.release()
