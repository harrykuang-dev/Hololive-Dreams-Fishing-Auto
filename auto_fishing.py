"""Vision-based auto fishing for hololive-Dreams on Windows.

The bot watches the game's client area, clicks the short-lived TAP prompt, and
uses feedback control during the reeling minigame.  It does not read or modify
game memory.
"""

from __future__ import annotations

import argparse
import ctypes
import signal
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
import win32api
import win32con
import win32gui
import win32ui
from fishing_auto.vision import save_image
from bot_vision import Detection, analyze
from bot_control import ReelTracker, ReelControl, Navigation, BiteGuard, CatchLedger


def enable_dpi_awareness() -> None:
    """Make Win32 coordinates match physical screenshot pixels."""
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()


class WindowCapture:
    def __init__(self, title: str) -> None:
        self.title = title
        self.hwnd = win32gui.FindWindow(None, title)
        if not self.hwnd:
            raise RuntimeError(f"找不到視窗：{title!r}")
        self._dc = self._source = self._memory = self._bitmap = self._previous = None
        self._size = None
        self._capture_rect = None

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
        rect = self.client_rect()
        x1,y1,x2,y2 = rect
        width,height = x2-x1,y2-y1
        if self._size != (width,height):
            self.close()
            try:
                self._dc = win32gui.GetDC(0)
                self._source = win32ui.CreateDCFromHandle(self._dc)
                self._memory = self._source.CreateCompatibleDC()
                self._bitmap = win32ui.CreateBitmap()
                self._bitmap.CreateCompatibleBitmap(self._source,width,height)
                self._previous = self._memory.SelectObject(self._bitmap)
                self._size = (width,height)
            except Exception:
                self.close()
                raise
        # Reuse the client-sized GDI buffer instead of capturing/converting
        # the entire desktop each frame. It remains ordinary screen pixels.
        self._memory.BitBlt((0,0),(width,height),self._source,(x1,y1),win32con.SRCCOPY)
        if self.client_rect() != rect:
            raise RuntimeError("擷取期間遊戲視窗移動／縮放，已停止。")
        self._capture_rect = rect
        return np.frombuffer(self._bitmap.GetBitmapBits(True),np.uint8).reshape(height,width,4)[:,:,:3].copy()

    def close(self):
        if self._memory and self._previous is not None:
            self._memory.SelectObject(self._previous)
        if self._bitmap:
            win32gui.DeleteObject(self._bitmap.GetHandle())
        if self._memory:
            self._memory.DeleteDC()
        if self._dc is not None:
            win32gui.ReleaseDC(0,self._dc)
        self._dc = self._source = self._memory = self._bitmap = self._previous = None
        self._size = None
        self._capture_rect = None

    def screen_point(self, point: tuple[float, float]) -> tuple[int, int]:
        x1, y1, x2, y2 = self.client_rect()
        if (x1,y1,x2,y2) != self._capture_rect:
            raise RuntimeError("遊戲視窗位置已改變，請重新開始。")
        if not (0 <= point[0] < x2-x1 and 0 <= point[1] < y2-y1):
            raise RuntimeError("操作座標超出遊戲客戶區，已停止。")
        return int(x1 + point[0]), int(y1 + point[1])


class MouseController:
    def __init__(self, window: WindowCapture) -> None:
        self.window = window
        self.held = False
        self.original_position = win32api.GetCursorPos()

    def _move_client(self, point: tuple[float, float]) -> None:
        screen = self.window.screen_point(point)
        root = win32gui.GetAncestor(win32gui.WindowFromPoint(screen),win32con.GA_ROOT)
        if root != self.window.hwnd:
            raise RuntimeError("操作位置被其他視窗遮擋，已停止。")
        win32api.SetCursorPos(screen)

    def click(self, point: tuple[float, float], duration: float = .065) -> None:
        self.release()
        self._move_client(point)
        if win32gui.GetForegroundWindow() != self.window.hwnd:
            return
        self.held = True
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            time.sleep(duration)
        finally:
            self.release()

    def press(self, point: tuple[float, float]) -> None:
        if win32gui.GetForegroundWindow() != self.window.hwnd:
            self.release()
            return
        if self.held:
            return
        self._move_client(point)
        if win32gui.GetForegroundWindow() != self.window.hwnd:
            return
        self.held = True
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
        except Exception:
            self.release()
            raise

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
    from app_locale import text as tr
    language = getattr(args, 'language', 'auto')
    target_streak = getattr(args, 'target_streak', 0)
    if target_streak < 0:
        raise ValueError("target_streak must be non-negative")

    def msg(key: str, **values) -> str:
        return tr(language, key, **values)

    def emit(message: str) -> None:
        if status_callback:
            status_callback(message)
        if sys.stdout is not None:
            print(message, flush=True)

    window = WindowCapture(args.window_title)
    window.activate()
    time.sleep(0.20)
    mouse = MouseController(window)
    running = True

    def stop_handler(_signum, _frame):
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
    tracker = ReelTracker()
    controller = ReelControl(lead=args.lead)
    navigation = Navigation()
    bite_guard = BiteGuard()
    ledger = CatchLedger()
    start_time = time.perf_counter()
    frame_period = 1.0 / args.fps
    frame_count = 0
    previous_state = ""
    last_debug = 0.
    minigame_seen = False
    lost_since = None
    trace_file = None
    video = None
    if debug_dir:
        trace_file = (debug_dir / "trace.csv").open("w", encoding="utf-8", newline="")
        trace_file.write("seconds,state,fish_y,player_y,bar_h,player_v,fish_v,error,control,held,predicted,scene,attempts\n")
    labels = {scene: msg(scene) for scene in
              ('reward', 'reward_continue', 'encyclopedia', 'item_detail', 'action', 'result_continue')}
    emit(msg('connected_window', title=args.window_title, language=language))
    try:
        while running and not (stop_event and stop_event.is_set()):
            loop_started = time.perf_counter()
            if args.max_seconds and loop_started-start_time >= args.max_seconds:
                emit(msg('timeout'))
                break
            if win32api.GetAsyncKeyState(win32con.VK_F9) & 0x8001:
                emit(msg('f9_stop'))
                break
            if win32gui.GetForegroundWindow() != window.hwnd:
                mouse.release()
                emit(msg('focus_lost'))
                break
            frame = window.grab()
            height,width = frame.shape[:2]
            if abs(width/height-16/9)>.10:
                emit(msg('aspect_stop'))
                break
            d = analyze(frame, language)
            now = time.perf_counter()
            if d.catch_result and ledger.catch_seen():
                emit(msg('catch_confirmed', round=ledger.rounds, streak=ledger.streak))
                if debug_dir:
                    save_image(debug_dir/f"catch_{ledger.catches:03d}.png",frame)
                if target_streak and ledger.streak >= target_streak:
                    emit(msg('target_reached', target=target_streak))
                    break
            bite = bite_guard.update(d,now)
            tracking = tracker.update(d,now,height)
            control_error = None
            control_mode = ""
            # Feed all scenes to navigation so disappearance confirms the
            # previous UI action. No one-shot action_armed latch.
            action = navigation.update(d,now)
            if navigation.confirmed:
                emit(msg('switched_scene', scene=labels.get(navigation.confirmed, navigation.confirmed)))
                navigation.confirmed = None
            if d.track_present:
                if not minigame_seen:
                    if ledger.reel_started():
                        emit(msg('lost_streak', failed=ledger.failed))
                    emit(msg('reel_started', round=ledger.rounds))
                minigame_seen = True
                lost_since = None
                if tracking:
                    state = msg('reeling')
                    pressed,control_mode,control_error = controller.decide(tracking,height)
                    reel_point = (.86*width,.82*height)
                    if pressed:
                        mouse.press(reel_point)
                    else:
                        mouse.release()
                else:
                    state = msg('tracking_lost')
                    mouse.release()
                    controller.reset()
            else:
                mouse.release()
                controller.reset()
                if minigame_seen and lost_since is None:
                    lost_since = now
                if args.once and lost_since is not None and now-lost_since>1.2:
                    emit(msg('once_done'))
                    break
                if action == 'blocked':
                    emit(msg('retry_stop', scene=labels.get(d.scene,d.scene)))
                    break
                if isinstance(action,tuple) and not args.once:
                    state = labels.get(d.scene, msg('action'))
                    emit(msg('click_action', scene=state, x=round(action[0]),
                             y=round(action[1]), attempt=navigation.attempts))
                    mouse.click(action)
                elif bite:
                    state = msg('tap')
                    mouse.click((.50*width,.50*height), duration=.045)
                    minigame_seen = False
                    lost_since = None
                else:
                    state = msg('ending') if lost_since is not None and now-lost_since<1.2 else msg('waiting')
            if state != previous_state:
                emit(msg('state_prefix') + state)
                previous_state = state
                if debug_dir:
                    save_image(debug_dir/f"{frame_count:06d}_{d.scene}.png",annotate(frame,d,d.scene))
            if debug_dir:
                if getattr(args,'record',False) and video is None:
                    video = cv2.VideoWriter(str(debug_dir/"game.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),
                                            args.fps,(width,height))
                if video and video.isOpened():
                    video.write(frame)
                if now-last_debug>.5:
                    save_image(debug_dir/"latest.png",annotate(frame,d,d.scene))
                    last_debug = now
                if d.action_button and frame_count % 8 == 0:
                    save_image(debug_dir/f"ui_{frame_count:06d}_{d.scene}.png",frame)
            if trace_file:
                values = (tracking.fish,tracking.player,tracking.bar_height,
                          tracking.player_velocity,tracking.fish_velocity) if tracking else ("",)*5
                trace_file.write(f"{now-start_time:.4f},{state},"+",".join(str(v) for v in values)+
                                 f",{control_error if control_error is not None else ''},{control_mode},"
                                 f"{int(mouse.held)},{int(bool(tracking and tracking.predicted))},"
                                 f"{d.scene},{navigation.attempts}\n")
                if frame_count%30==0:
                    trace_file.flush()
            frame_count += 1
            remaining = frame_period-(time.perf_counter()-loop_started)
            if remaining>0:
                if stop_event:
                    stop_event.wait(remaining)
                else:
                    time.sleep(remaining)
    finally:
        mouse.close()
        window.close()
        if trace_file:
            trace_file.close()
        if video:
            video.release()
    elapsed = time.perf_counter()-start_time
    emit(msg('final_stop', frames=frame_count, seconds=elapsed, rounds=ledger.rounds,
             catches=ledger.catches, streak=ledger.streak))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="hololive-Dreams 視覺自動釣魚")
    parser.add_argument("--window-title", default="hololive-Dreams")
    from app_locale import GAME_LANGUAGES
    parser.add_argument("--language", choices=("auto", *GAME_LANGUAGES.values()), default="auto",
                        help="遊戲介面語言（auto 或遊戲支援的六種語言）")
    parser.add_argument("--fps", type=float, default=40.0, help="辨識頻率")
    parser.add_argument(
        "--lead", type=float, default=0.20, help="滑塊煞車提前量（秒）"
    )
    parser.add_argument(
        "--deadband", type=float, default=0.018, help="垂直控制死區（畫面高度比例）"
    )
    parser.add_argument(
        "--pulse-hz", type=float, default=7.0, help="接近魚時的基準連點頻率"
    )
    parser.add_argument("--once", action="store_true", help="完成一輪拉扯後停止")
    parser.add_argument("--target-streak", type=int, default=0,
                        help="供實測使用：連續確認指定局數後停止；0 表示持續運行")
    parser.add_argument("--max-seconds", type=float, default=0.0)
    parser.add_argument("--debug-dir", help="儲存狀態切換和最新辨識畫面")
    parser.add_argument("--record", action="store_true", help="另存實測影片（需 debug-dir）")
    return parser.parse_args()


if __name__ == "__main__":
    enable_dpi_awareness()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        raise SystemExit(run(args))
    except Exception as exc:
        from app_locale import text as tr
        print(f"{tr(args.language, 'error')}: {exc}", file=sys.stderr)
        raise
