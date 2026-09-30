from __future__ import annotations

import argparse
import queue
import threading
import os
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from auto_fishing import enable_dpi_awareness, run
from app_locale import GAME_LANGUAGES, text as tr


APP_VERSION = "0.3.0"


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
        self.root.title(f"Hololive Dreams v{APP_VERSION}")
        self.root.geometry("560x650")
        self.root.minsize(520, 620)
        self.root.configure(bg=self.BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.messages: queue.Queue[tuple[str, str | None]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self._closing = False
        self.game_language = tk.StringVar(value="繁體中文")
        self.session_args = self.bot_args("zh-TW")
        self.diagnostics = tk.BooleanVar(value=False)
        self.has_error = False

        self._build()
        self._apply_language()
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
        self.subtitle = tk.Label(
            header,
            bg=self.BG,
            fg=self.CYAN,
            font=("Microsoft JhengHei UI", 15, "bold"),
        )
        self.subtitle.pack(anchor="w", pady=(3, 0))

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
            text="",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Microsoft JhengHei UI", 16, "bold"),
        )
        self.status.pack(side="left", padx=(10, 0))

        self.instructions = tk.Label(
            card,
            bg=self.PANEL,
            fg=self.MUTED,
            justify="left",
            anchor="w",
            wraplength=480,
            font=("Microsoft JhengHei UI", 10),
        )
        self.instructions.pack(anchor="w", padx=20)

        language_row = tk.Frame(self.root,bg=self.BG)
        language_row.pack(fill="x",padx=30,pady=(0,12))
        self.language_label = tk.Label(language_row,bg=self.BG,fg=self.TEXT,
                                       font=("Microsoft JhengHei UI",10))
        self.language_label.pack(side="left",padx=(0,12))
        self.language_choice = ttk.Combobox(
            language_row,textvariable=self.game_language,state="readonly",
            values=tuple(GAME_LANGUAGES),width=17,
        )
        self.language_choice.pack(side="left")
        self.language_choice.bind("<<ComboboxSelected>>",self._apply_language)
        controls = tk.Frame(self.root, bg=self.BG)
        controls.pack(fill="x", padx=30, pady=(0, 18))
        self.start_button = tk.Button(
            controls,
            text="",
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
            text="",
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
        self.diagnostics_check = tk.Checkbutton(
            self.root,
            variable=self.diagnostics,bg=self.BG,fg=self.MUTED,
            activebackground=self.BG,activeforeground=self.TEXT,
            selectcolor=self.PANEL,highlightthickness=0,wraplength=480,
        )
        self.diagnostics_check.pack(anchor="w",padx=30,pady=(0,8))

        log_card = tk.Frame(
            self.root,
            bg=self.PANEL,
            highlightthickness=1,
            highlightbackground="#213651",
        )
        log_card.pack(fill="both", expand=True, padx=30, pady=(0, 18))
        self.log_title = tk.Label(
            log_card,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Microsoft JhengHei UI", 11, "bold"),
        )
        self.log_title.pack(anchor="w", padx=16, pady=(13, 7))
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

        self.footer = tk.Label(
            self.root,
            bg=self.BG,
            fg="#60748e",
            wraplength=500,
            font=("Microsoft JhengHei UI", 9),
        )
        self.footer.pack(pady=(0, 18))

    def _apply_language(self, _event=None) -> None:
        lang = self.language_code()
        self.root.title(f"Hololive Dreams {tr(lang,'subtitle')} v{APP_VERSION}")
        self.subtitle.configure(text=tr(lang,"subtitle"))
        self.instructions.configure(text=tr(lang,"instructions"))
        self.language_label.configure(text=tr(lang,"game_language"))
        self.start_button.configure(text=tr(lang,"start"))
        self.stop_button.configure(text=tr(lang,"stop"))
        self.diagnostics_check.configure(text=tr(lang,"diagnostics"))
        self.log_title.configure(text=tr(lang,"log"))
        self.footer.configure(text=f"v{APP_VERSION}  ·  {tr(lang,'footer')}")
        if not self.worker or not self.worker.is_alive():
            self._set_status(tr(lang,"error" if self.has_error else "idle"),
                             self.RED if self.has_error else self.MUTED)

    @staticmethod
    def bot_args(language: str = "auto") -> argparse.Namespace:
        return argparse.Namespace(
            window_title="hololive-Dreams",
            language=language,
            fps=40.0,
            lead=0.20,
            deadband=0.018,
            pulse_hz=7.0,
            once=False,
            target_streak=0,
            max_seconds=0.0,
            debug_dir=None,
            record=False,
        )

    def language_code(self) -> str:
        return GAME_LANGUAGES[self.game_language.get()]

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
        lang = self.language_code()
        self.has_error = False
        self._set_status(tr(lang,"connecting"), self.CYAN)
        self._append_log(tr(lang,"started",language=self.game_language.get()))
        self.session_args = self.bot_args(lang)
        self.language_choice.configure(state="disabled")
        if self.diagnostics.get():
            base = Path(os.environ.get('LOCALAPPDATA',str(Path.cwd())))
            directory = base/'HololiveFishingAuto'/'sessions'/time.strftime('%Y%m%d-%H%M%S')
            self.session_args.debug_dir = str(directory)
            self._append_log(tr(lang,"diagnostic_path",path=directory))
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
            self._set_status(tr(self.session_args.language,"stopping"), self.MUTED)

    def _poll(self) -> None:
        try:
            while True:
                kind, value = self.messages.get_nowait()
                lang = self.session_args.language
                if kind == "log" and value:
                    self._append_log(value)
                    prefix = tr(lang,"state_prefix")
                    if value.startswith(prefix):
                        state = value[len(prefix):]
                        colors = {
                            tr(lang,"waiting"): self.CYAN,
                            tr(lang,"tap"): "#ffd65c",
                            tr(lang,"reeling"): self.GREEN,
                            tr(lang,"tracking_lost"): "#ffd65c",
                            tr(lang,"ending"): "#c7a7ff",
                            tr(lang,"button"): self.CYAN,
                        }
                        self._set_status(state, colors.get(state, self.CYAN))
                    elif value == tr(lang, "connected_window", title=self.session_args.window_title, language=lang):
                        self._set_status(tr(lang,"connected"), self.GREEN)
                elif kind == "error":
                    self.has_error = True
                    self._append_log(f"{tr(lang,'error')}: {value}")
                    self._set_status(tr(lang,"error"), self.RED)
                    if not self._closing:
                        messagebox.showerror(tr(lang,"error_title"), value or tr(lang,"unknown_error"))
                elif kind == "done":
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    self.language_choice.configure(state="readonly")
                    if not self.has_error:
                        self._set_status(tr(lang,"stopped"), self.MUTED)
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
