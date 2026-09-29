from __future__ import annotations

import argparse
import queue
import threading
import os
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from auto_fishing import enable_dpi_awareness, run


APP_VERSION = "0.2.2"


class FishingApp:
    BG = "#08111f"
    PANEL = "#101d30"
    PANEL_2 = "#16263e"
    TEXT = "#f2f7ff"
    MUTED = "#91a4bd"
    CYAN = "#2cc9f5"
    CYAN_ACTIVE = "#6cddff"
    GREEN = "#52e3a4"
    RED = "#ff6b81"

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"Hololive Dreams 自動釣魚 v{APP_VERSION}")
        self.root.geometry("560x650")
        self.root.minsize(520, 620)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.messages: queue.Queue[tuple[str, str | None]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self._closing = False
        self.session_args = self.bot_args()
        self.diagnostics = tk.BooleanVar(value=False)

        self._build()
        self.root.after(100, self._poll)

    def _build(self) -> None:
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=30, pady=(26, 18))
        tk.Label(
            header,
            text="🎣  Hololive Dreams",
            bg=self.BG,
            fg=self.TEXT,
            font=("Microsoft JhengHei UI", 24, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="自動釣魚助手",
            bg=self.BG,
            fg=self.CYAN,
            font=("Microsoft JhengHei UI", 15, "bold"),
        ).pack(anchor="w", pady=(3, 0))

        card = tk.Frame(
            self.root,
            bg=self.PANEL,
            highlightthickness=1,
            highlightbackground="#213651",
        )
        card.pack(fill="x", padx=30, pady=(0, 18), ipady=14)

        status_row = tk.Frame(card, bg=self.PANEL)
        status_row.pack(fill="x", padx=20, pady=(2, 10))
        self.dot = tk.Label(
            status_row, text="●", bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 16)
        )
        self.dot.pack(side="left")
        self.status = tk.Label(
            status_row,
            text="待命",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Microsoft JhengHei UI", 16, "bold"),
        )
        self.status.pack(side="left", padx=(10, 0))

        tk.Label(
            card,
            text=(
                "請先開啟 hololive-Dreams，進入釣魚畫面後按下開始。\n"
                "自動拉扯、關閉圖鑑／獎勵並續竿。F9 可立即停止。"
            ),
            bg=self.PANEL,
            fg=self.MUTED,
            justify="left",
            font=("Microsoft JhengHei UI", 10),
        ).pack(anchor="w", padx=20)

        controls = tk.Frame(self.root, bg=self.BG)
        controls.pack(fill="x", padx=30, pady=(0, 18))
        self.start_button = tk.Button(
            controls,
            text="▶  開始釣魚",
            command=self.start,
            bg=self.CYAN,
            activebackground=self.CYAN_ACTIVE,
            fg="#042033",
            activeforeground="#042033",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Microsoft JhengHei UI", 15, "bold"),
            pady=14,
        )
        self.stop_button = tk.Button(
            controls,
            text="■  停止",
            command=self.stop,
            state="disabled",
            bg=self.PANEL_2,
            disabledforeground="#5d6d82",
            activebackground="#2b3c55",
            fg=self.TEXT,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Microsoft JhengHei UI", 12, "bold"),
            padx=24,
            pady=14,
        )
        self.stop_button.pack(side="right", padx=(12, 0))
        self.start_button.pack(side="left", fill="x", expand=True)
        tk.Checkbutton(
            self.root,text="儲存本機診斷（畫面與追蹤紀錄，不上傳）",
            variable=self.diagnostics,bg=self.BG,fg=self.MUTED,
            activebackground=self.BG,activeforeground=self.TEXT,
            selectcolor=self.PANEL,highlightthickness=0,
        ).pack(anchor="w",padx=30,pady=(0,8))

        log_card = tk.Frame(
            self.root,
            bg=self.PANEL,
            highlightthickness=1,
            highlightbackground="#213651",
        )
        log_card.pack(fill="both", expand=True, padx=30, pady=(0, 18))
        tk.Label(
            log_card,
            text="運行紀錄",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Microsoft JhengHei UI", 11, "bold"),
        ).pack(anchor="w", padx=16, pady=(13, 7))
        self.log = tk.Text(
            log_card,
            bg="#0b1626",
            fg="#b8c7d9",
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
            padx=12,
            pady=10,
            height=12,
        )
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        tk.Label(
            self.root,
            text=(
                f"v{APP_VERSION}  ·  僅使用畫面辨識與滑鼠輸入  ·  "
                "切換視窗會自動停止"
            ),
            bg=self.BG,
            fg="#60748e",
            font=("Microsoft JhengHei UI", 9),
        ).pack(pady=(0, 18))

    @staticmethod
    def bot_args() -> argparse.Namespace:
        return argparse.Namespace(
            window_title="hololive-Dreams",
            fps=40.0,
            lead=0.20,
            deadband=0.018,
            pulse_hz=7.0,
            once=False,
            max_seconds=0.0,
            debug_dir=None,
            record=False,
        )

    def _append_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        if int(self.log.index('end-1c').split('.')[0])>1000:
            self.log.delete('1.0','101.0')
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_status(self, text: str, color: str) -> None:
        self.status.configure(text=text)
        self.dot.configure(fg=color)

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._set_status("正在連接遊戲…", self.CYAN)
        self._append_log("開始自動釣魚")
        self.session_args = self.bot_args()
        if self.diagnostics.get():
            base = Path(os.environ.get('LOCALAPPDATA',str(Path.cwd())))
            directory = base/'HololiveFishingAuto'/'sessions'/time.strftime('%Y%m%d-%H%M%S')
            self.session_args.debug_dir = str(directory)
            self._append_log(f"本機診斷：{directory}")
        self.worker = threading.Thread(
            target=self._run_bot, name="fishing-bot", daemon=True
        )
        self.worker.start()

    def _run_bot(self) -> None:
        try:
            run(
                self.session_args,
                stop_event=self.stop_event,
                status_callback=lambda text: self.messages.put(("log", text)),
            )
        except Exception as exc:
            self.messages.put(("error", str(exc)))
        finally:
            self.messages.put(("done", None))

    def stop(self) -> None:
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.stop_button.configure(state="disabled")
            self._set_status("正在停止…", self.MUTED)

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == "log" and value:
                    self._append_log(value)
                    if value.startswith("狀態："):
                        state = value.split("：", 1)[1].split(" ", 1)[0]
                        colors = {
                            "等待": self.CYAN,
                            "TAP": "#ffd65c",
                            "拉扯": self.GREEN,
                            "追蹤暫失": "#ffd65c",
                            "收尾動畫": "#c7a7ff",
                            "按鈕": self.CYAN,
                        }
                        self._set_status(state, colors.get(state, self.CYAN))
                    elif value.startswith("已連接視窗"):
                        self._set_status("已連接", self.GREEN)
                elif kind == "error":
                    self._append_log(f"錯誤：{value}")
                    self._set_status("發生錯誤", self.RED)
                    if not self._closing:
                        messagebox.showerror("無法開始自動釣魚", value or "未知錯誤")
                elif kind == "done":
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    if self.status.cget("text") != "發生錯誤":
                        self._set_status("已停止", self.MUTED)
        except queue.Empty:
            pass

        if not self._closing:
            self.root.after(100, self._poll)

    def close(self) -> None:
        self._closing = True
        self.stop_event.set()
        self.root.after(150, self._finish_close)

    def _finish_close(self) -> None:
        if self.worker and self.worker.is_alive():
            self.root.after(100, self._finish_close)
        else:
            self.root.destroy()


def main() -> None:
    enable_dpi_awareness()
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.15)
    except tk.TclError:
        pass
    FishingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
