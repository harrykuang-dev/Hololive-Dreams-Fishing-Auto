"""Vision-based auto fishing for hololive-Dreams on Windows.

The bot watches the game's client area, clicks the short-lived TAP prompt, and
uses feedback control during the reeling minigame.  It does not read or modify
game memory.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import win32api
import win32con
import win32gui
from PIL import ImageGrab


def enable_dpi_awareness() -> None:
    """Make Win32 coordinates match physical screenshot pixels."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()


@dataclass
class Detection:
    tap: bool = False
    tap_pixels: int = 0
    player_center: tuple[float, float] | None = None
    player_box: tuple[int, int, int, int] | None = None
    fish_center: tuple[float, float] | None = None
    fish_box: tuple[int, int, int, int] | None = None
    track_present: bool = False
    action_button: tuple[float, float] | None = None

    @property
    def minigame(self) -> bool:
        return (
            self.track_present
            and self.player_center is not None
            and self.fish_center is not None
        )


class WindowCapture:
    def __init__(self, title: str) -> None:
        self.title = title
        self.hwnd = win32gui.FindWindow(None, title)
        if not self.hwnd:
            raise RuntimeError(f"找不到視窗：{title!r}")

    def activate(self) -> None:
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        try:
            # A brief Alt press allows SetForegroundWindow under Windows'
            # foreground-lock rules without opening any system UI.
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32gui.SetForegroundWindow(self.hwnd)
        finally:
            win32api.keybd_event(
                win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0
            )

    def client_rect(self) -> tuple[int, int, int, int]:
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        x1, y1 = win32gui.ClientToScreen(self.hwnd, (left, top))
        x2, y2 = win32gui.ClientToScreen(self.hwnd, (right, bottom))
        if x2 <= x1 or y2 <= y1:
            raise RuntimeError("遊戲視窗沒有可擷取的客戶區域")
        return x1, y1, x2, y2

    def grab(self) -> np.ndarray:
        rgb = np.asarray(ImageGrab.grab(self.client_rect(), all_screens=True))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    def screen_point(self, point: tuple[float, float]) -> tuple[int, int]:
        x1, y1, x2, y2 = self.client_rect()
        return int(x1 + point[0]), int(y1 + point[1])


class MouseController:
    def __init__(self, window: WindowCapture) -> None:
        self.window = window
        self.held = False
        self.original_position = win32api.GetCursorPos()

    def _move_client(self, point: tuple[float, float]) -> None:
        win32api.SetCursorPos(self.window.screen_point(point))

    def click(self, point: tuple[float, float]) -> None:
        self.release()
        self._move_client(point)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def tap(self, point: tuple[float, float], duration: float = 0.018) -> None:
        """Send a short but game-visible reel pulse."""
        self.release()
        self._move_client(point)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        time.sleep(duration)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

    def press(self, point: tuple[float, float]) -> None:
        if self.held:
            return
        self._move_client(point)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        self.held = True

    def release(self) -> None:
        if not self.held:
            return
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
        self.held = False

    def close(self) -> None:
        self.release()
        try:
            win32api.SetCursorPos(self.original_position)
        except Exception:
            pass


def _components(mask: np.ndarray, offset: tuple[int, int]) -> list[dict[str, float]]:
    count, _labels, stats, centers = cv2.connectedComponentsWithStats(mask)
    ox, oy = offset
    result: list[dict[str, float]] = []
    for i in range(1, count):
        x, y, w, h, area = stats[i]
        cx, cy = centers[i]
        result.append(
            {
                "x": float(x + ox),
                "y": float(y + oy),
                "w": float(w),
                "h": float(h),
                "area": float(area),
                "cx": float(cx + ox),
                "cy": float(cy + oy),
            }
        )
    return result


def analyze(frame: np.ndarray) -> Detection:
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    detection = Detection()

    # The magenta exclamation badge is far more stable than OCR on "TAP!".
    tx0, tx1 = int(0.40 * w), int(0.82 * w)
    ty0, ty1 = int(0.30 * h), int(0.90 * h)
    tap_roi = hsv[ty0:ty1, tx0:tx1]
    tap_mask = cv2.inRange(
        tap_roi, np.array((140, 100, 150)), np.array((170, 255, 255))
    )
    detection.tap_pixels = int(cv2.countNonZero(tap_mask))
    detection.tap = detection.tap_pixels > max(700, int(w * h * 0.00035))

    # Fishing UI is anchored on the right side.  Restricting the search region
    # prevents scenery and character colors from becoming false positives.
    rx0, rx1 = int(0.55 * w), int(0.82 * w)
    ry0, ry1 = int(0.10 * h), int(0.93 * h)
    roi = hsv[ry0:ry1, rx0:rx1]

    gold = cv2.inRange(
        roi, np.array((10, 70, 60)), np.array((24, 255, 255))
    )
    gold = cv2.morphologyEx(gold, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    for c in _components(gold, (rx0, ry0)):
        if (
            c["h"] > 0.45 * h
            and 0.02 * w <= c["w"] <= 0.15 * w
            and c["area"] > w * h * 0.003
        ):
            detection.track_present = True
            break

    yellow = cv2.inRange(
        roi, np.array((20, 110, 170)), np.array((35, 255, 255))
    )
    # The fish sprite can temporarily cover the middle of the yellow bar and
    # split it into two blobs. A narrow vertical closing kernel reconnects the
    # two halves without joining the neighboring brown track border.
    yellow = cv2.morphologyEx(
        yellow,
        cv2.MORPH_CLOSE,
        np.ones((max(7, int(0.085 * h)), 3), np.uint8),
    )
    player_candidates = []
    for c in _components(yellow, (rx0, ry0)):
        if (
            c["area"] > w * h * 0.00035
            and 0.014 * w <= c["w"] <= 0.075 * w
            and 0.055 * h <= c["h"] <= 0.29 * h
            and c["h"] > c["w"] * 1.45
        ):
            player_candidates.append(c)
    if player_candidates:
        player = max(
            player_candidates,
            key=lambda c: c["area"] - abs(c["cx"] - 0.69 * w) * 2.0,
        )
        detection.player_center = (player["cx"], player["cy"])
        detection.player_box = (
            int(player["x"]),
            int(player["y"]),
            int(player["w"]),
            int(player["h"]),
        )

    cyan = cv2.inRange(
        roi, np.array((84, 75, 165)), np.array((100, 255, 255))
    )
    cyan = cv2.morphologyEx(cyan, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    fish_candidates = []
    for c in _components(cyan, (rx0, ry0)):
        if (
            c["area"] > w * h * 0.00010
            and 0.014 * w <= c["w"] <= 0.085 * w
            and 0.014 * h <= c["h"] <= 0.105 * h
            and 0.55 <= c["w"] / max(c["h"], 1.0) <= 3.2
        ):
            fish_candidates.append(c)
    if fish_candidates:
        expected_x = (
            detection.player_center[0] if detection.player_center else 0.69 * w
        )
        fish = max(
            fish_candidates,
            key=lambda c: c["area"] - abs(c["cx"] - expected_x) * 8.0,
        )
        detection.fish_center = (fish["cx"], fish["cy"])
        detection.fish_box = (
            int(fish["x"]),
            int(fish["y"]),
            int(fish["w"]),
            int(fish["h"]),
        )
    if (
        detection.player_center
        and detection.fish_center
        and abs(detection.player_center[0] - detection.fish_center[0])
        > 0.04 * w
    ):
        # Real minigame markers share one vertical track. This rejects cyan
        # scenery and yellow fishing rods during the post-catch animation.
        detection.fish_center = None
        detection.fish_box = None

    # Menu, failure, and result screens all expose a large cyan action button
    # near the lower-right corner.  Selecting the right-most candidate avoids
    # the failure screen's Cancel button.
    bx0, bx1 = int(0.44 * w), int(0.98 * w)
    by0, by1 = int(0.72 * h), int(0.98 * h)
    button_roi = hsv[by0:by1, bx0:bx1]
    button_mask = cv2.inRange(
        button_roi, np.array((84, 80, 175)), np.array((105, 255, 255))
    )
    button_mask = cv2.morphologyEx(
        button_mask, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8)
    )
    buttons = []
    for c in _components(button_mask, (bx0, by0)):
        fill = c["area"] / max(c["w"] * c["h"], 1.0)
        if (
            c["area"] > w * h * 0.0015
            and 0.09 * w <= c["w"] <= 0.38 * w
            and 0.035 * h <= c["h"] <= 0.18 * h
            and fill > 0.35
            and c["cx"] > 0.68 * w
            and c["cy"] > 0.82 * h
        ):
            buttons.append(c)
    if buttons:
        button = max(buttons, key=lambda c: (c["cx"], c["area"]))
        detection.action_button = (button["cx"], button["cy"])

    return detection


def annotate(frame: np.ndarray, detection: Detection, state: str) -> np.ndarray:
    out = frame.copy()
    for box, color in (
        (detection.player_box, (0, 255, 255)),
        (detection.fish_box, (255, 255, 0)),
    ):
        if box:
            x, y, w, h = box
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 3)
    if detection.action_button:
        cv2.circle(
            out,
            (int(detection.action_button[0]), int(detection.action_button[1])),
            15,
            (0, 255, 0),
            3,
        )
    cv2.putText(
        out,
        f"{state} tap={detection.tap_pixels}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    return out


def run(
    args: argparse.Namespace,
    stop_event: threading.Event | None = None,
    status_callback=None,
) -> int:
    def emit(message: str) -> None:
        if status_callback:
            status_callback(message)
        # PyInstaller's --windowed mode deliberately sets stdout/stderr to
        # None.  Keep console logging for source/CLI runs without crashing the
        # GUI executable.
        if sys.stdout is not None:
            print(message, flush=True)

    window = WindowCapture(args.window_title)
    window.activate()
    time.sleep(0.20)
    mouse = MouseController(window)
    running = True

    def stop_handler(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False
        if stop_event:
            stop_event.set()

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, stop_handler)
        signal.signal(signal.SIGTERM, stop_handler)

    debug_dir = Path(args.debug_dir) if args.debug_dir else None
    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)

    previous_state = "啟動"
    previous_player: tuple[float, float] | None = None
    previous_fish: tuple[float, float] | None = None
    filtered_player_velocity = 0.0
    filtered_fish_velocity = 0.0
    last_tracking_time: float | None = None
    last_action = 0.0
    last_debug = 0.0
    last_pulse = 0.0
    action_button_since: float | None = None
    minigame_seen = False
    minigame_lost_since: float | None = None
    action_armed = True
    start_time = time.perf_counter()
    frame_period = 1.0 / args.fps
    frame_count = 0
    trace_file = None
    if debug_dir:
        trace_file = (debug_dir / "trace.csv").open(
            "w", encoding="utf-8", newline=""
        )
        trace_file.write("seconds,state,fish_y,player_y,error,control,held\n")

    emit(f"已連接視窗：{args.window_title}")
    try:
        while running and not (stop_event and stop_event.is_set()):
            loop_started = time.perf_counter()
            if args.max_seconds and loop_started - start_time >= args.max_seconds:
                emit("已達執行時間上限。")
                break
            if win32gui.GetForegroundWindow() != window.hwnd:
                mouse.release()
                emit("遊戲失去焦點，為避免點到其他視窗，程式已停止。")
                break

            frame = window.grab()
            height, width = frame.shape[:2]
            detection = analyze(frame)
            now = time.perf_counter()
            if detection.action_button:
                if action_button_since is None:
                    action_button_since = now
            else:
                action_button_since = None
            action_button_ready = (
                action_button_since is not None
                and now - action_button_since >= 0.20
            )
            control_error: float | None = None
            control_mode = ""

            if detection.minigame:
                state = "拉扯"
                minigame_seen = True
                minigame_lost_since = None
                action_armed = False
                reel_point = (0.86 * width, 0.82 * height)
                player_y = detection.player_center[1]
                fish_y = detection.fish_center[1]

                if last_tracking_time is not None and previous_player and previous_fish:
                    dt = max(0.001, now - last_tracking_time)
                    instant_player_v = (player_y - previous_player[1]) / dt
                    instant_fish_v = (fish_y - previous_fish[1]) / dt
                    filtered_player_velocity = (
                        0.70 * filtered_player_velocity + 0.30 * instant_player_v
                    )
                    filtered_fish_velocity = (
                        0.70 * filtered_fish_velocity + 0.30 * instant_fish_v
                    )

                predicted_player = player_y + filtered_player_velocity * args.lead
                predicted_fish = fish_y + filtered_fish_velocity * args.lead * 0.65
                error = predicted_player - predicted_fish
                control_error = error
                player_half_height = detection.player_box[3] * 0.5
                # The fish only needs to remain inside the yellow bar.  Using
                # part of that available height as hysteresis is more stable
                # than chasing exact center alignment on every frame.
                near_band = max(
                    args.deadband * height, player_half_height * 0.48
                )

                if error > near_band:
                    # The yellow bar is well below the fish: rise quickly.
                    control_mode = "hold"
                    mouse.press(reel_point)
                elif error < -near_band:
                    # The yellow bar is well above the fish: fall quickly.
                    control_mode = "release"
                    mouse.release()
                else:
                    # Near the fish, short pulses avoid the large oscillations
                    # caused by alternating full hold and full release.
                    control_mode = "pulse"
                    mouse.release()
                    normalized_error = error / max(near_band, 1.0)
                    pulse_hz = float(
                        np.clip(
                            args.pulse_hz + normalized_error * 4.0,
                            2.5,
                            13.0,
                        )
                    )
                    if now - last_pulse >= 1.0 / pulse_hz:
                        mouse.tap(reel_point)
                        last_pulse = now

                previous_player = detection.player_center
                previous_fish = detection.fish_center
                last_tracking_time = now
            else:
                mouse.release()
                previous_player = None
                previous_fish = None
                last_tracking_time = None
                filtered_player_velocity = 0.0
                filtered_fish_velocity = 0.0

                if minigame_seen:
                    if minigame_lost_since is None:
                        minigame_lost_since = now
                        action_armed = True
                    state = "收尾動畫"
                    if args.once and now - minigame_lost_since > 1.0:
                        emit("單次拉扯已結束。")
                        break
                    if (
                        not args.once
                        and now - minigame_lost_since > 0.20
                        and action_button_ready
                        and now - last_action > 1.2
                    ):
                        state = "繼續"
                        mouse.click(detection.action_button)
                        last_action = now
                        minigame_seen = False
                        minigame_lost_since = None
                        action_armed = False
                    elif not args.once and now - minigame_lost_since > 12.0:
                        # Fall back to the regular menu/result classifier if a
                        # transition animation took an unusually long time.
                        minigame_seen = False
                        minigame_lost_since = None
                elif detection.tap and now - last_action > 0.6:
                    state = "TAP"
                    mouse.click((0.50 * width, 0.50 * height))
                    last_action = now
                    action_armed = False
                elif (
                    action_armed
                    and action_button_ready
                    and now - last_action > 1.2
                ):
                    state = "繼續" if minigame_seen else "按鈕"
                    mouse.click(detection.action_button)
                    last_action = now
                    action_armed = False
                else:
                    state = "等待"

            if state != previous_state:
                detail = ""
                if detection.minigame:
                    detail = (
                        f" 魚={detection.fish_center[1]:.0f} "
                        f"控制塊={detection.player_center[1]:.0f}"
                    )
                emit(f"狀態：{state}{detail}")
                previous_state = state
                if debug_dir:
                    stamp = time.strftime("%H%M%S")
                    cv2.imwrite(
                        str(debug_dir / f"{stamp}_{frame_count:06d}_{state}.png"),
                        annotate(frame, detection, state),
                    )

            if debug_dir and now - last_debug > 0.5:
                cv2.imwrite(
                    str(debug_dir / "latest.png"), annotate(frame, detection, state)
                )
                last_debug = now

            if trace_file:
                fish_y_text = (
                    f"{detection.fish_center[1]:.2f}"
                    if detection.fish_center
                    else ""
                )
                player_y_text = (
                    f"{detection.player_center[1]:.2f}"
                    if detection.player_center
                    else ""
                )
                error_text = (
                    f"{control_error:.2f}" if control_error is not None else ""
                )
                trace_file.write(
                    f"{now - start_time:.3f},{state},{fish_y_text},"
                    f"{player_y_text},{error_text},{control_mode},"
                    f"{int(mouse.held)}\n"
                )
                if frame_count % 24 == 0:
                    trace_file.flush()

            frame_count += 1
            remaining = frame_period - (time.perf_counter() - loop_started)
            if remaining > 0:
                time.sleep(remaining)
    finally:
        mouse.close()
        if trace_file:
            trace_file.close()

    elapsed = time.perf_counter() - start_time
    emit(f"停止：{frame_count} 幀 / {elapsed:.1f} 秒")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="hololive-Dreams 視覺自動釣魚")
    parser.add_argument("--window-title", default="hololive-Dreams")
    parser.add_argument("--fps", type=float, default=24.0, help="辨識頻率")
    parser.add_argument(
        "--lead", type=float, default=0.12, help="位置預測提前量（秒）"
    )
    parser.add_argument(
        "--deadband", type=float, default=0.018, help="垂直控制死區（畫面高度比例）"
    )
    parser.add_argument(
        "--pulse-hz", type=float, default=7.0, help="接近魚時的基準連點頻率"
    )
    parser.add_argument("--once", action="store_true", help="完成一輪拉扯後停止")
    parser.add_argument("--max-seconds", type=float, default=0.0)
    parser.add_argument("--debug-dir", help="儲存狀態切換和最新辨識畫面")
    return parser.parse_args()


if __name__ == "__main__":
    enable_dpi_awareness()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(run(parse_args()))
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        raise
