from __future__ import annotations
import argparse
import ctypes
import os
import queue
import threading
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import font, messagebox, ttk
import win32api
from auto_fishing import enable_dpi_awareness, run
from app_locale import GAME_LANGUAGES, text as tr
from app_settings import FishingCounter, parse_stop_hotkey, captured_hotkey

APP_VERSION = '1.0.1'
PROJECT_URL = 'https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto'


def asset_path(name):
    return Path(__file__).resolve().parent/'assets'/name


def window_dpi(root):
    try:
        dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
        if dpi: return dpi
    except (AttributeError,OSError):
        pass
    return round(root.winfo_fpixels('1i'))


def window_work_area(root):
    try:
        area = win32api.GetMonitorInfo(win32api.MonitorFromWindow(root.winfo_id(),2))['Work']
        return area[2]-area[0],area[3]-area[1]
    except Exception:
        return root.winfo_screenwidth(),root.winfo_screenheight()


class FishingApp:
    BG,TEXT,MUTED = '#f3f3f3','#202020','#666666'
    CYAN,GREEN,RED = '#0067c0','#187b38','#b42318'

    def __init__(self,root):
        self.root = root
        root.configure(bg=self.BG)
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.dpi = window_dpi(root)
        self.scale = self.dpi/96
        self.spacing = 1.
        root.tk.call('tk','scaling',self.dpi/72)
        self._configure_fonts()
        self._set_window_size(self.px(640),self.px(760))
        self.messages = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None
        self._closing = self.has_error = False
        self.counter = FishingCounter()
        self.game_language = tk.StringVar(value='繁體中文')
        self.target = tk.StringVar(value='0')
        self.stop_key = tk.StringVar(value='F9')
        self.shortcut_display = tk.StringVar(value='F9')
        self._shortcut_capturing = False
        self._developer_help_dialog = None
        self.diagnostics = tk.BooleanVar(value=False)
        self.session_args = self.bot_args('zh-TW')
        self._build()
        self._apply_language()
        try: root.iconbitmap(default=str(asset_path('fish-clear.ico')))
        except tk.TclError: pass
        root.bind('<Configure>',self._dpi_changed,add='+')
        root.bind('<Configure>',self._fit_content,add='+')
        root.bind('<Button-1>',self._cancel_shortcut_on_click,add='+')
        root.after(100,self._poll)

    def px(self,value): return round(value*self.scale)
    def py(self,value): return round(value*self.scale*self.spacing)

    def _set_window_size(self,width,height):
        work_width,work_height = window_work_area(self.root)
        available_width = max(1,work_width-self.px(40))
        available_height = max(1,work_height-self.px(40))
        self.root.minsize(min(self.px(590),available_width),min(self.px(720),available_height))
        content_height = min(height,available_height)
        if not hasattr(self,'main_frame'):
            self.spacing = .5 if content_height/self.scale<680 else 1.
        self.root.geometry(f'{min(width,available_width)}x{content_height}')

    def _configure_fonts(self):
        for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkHeadingFont'):
            font.nametofont(name).configure(family='Segoe UI',size=12)
        font.nametofont('TkFixedFont').configure(family='Consolas',size=11)

    def _dpi_changed(self,event):
        if event.widget is not self.root: return
        dpi = window_dpi(self.root)
        if dpi==self.dpi: return
        old_scale = self.scale
        self.dpi,self.scale = dpi,dpi/96
        self.root.tk.call('tk','scaling',dpi/72)
        self._configure_fonts()
        self._scale_layout(self.scale/old_scale)
        self.style.configure('Title.TLabel',font=('Segoe UI',18,'bold'))
        self.style.configure('Count.TLabel',font=('Segoe UI',16,'bold'))
        self.style.configure('Action.TButton',padding=(self.px(12),self.py(10)))
        self.style.configure('Help.TButton',font=('Segoe UI',10),padding=(self.px(2),0))
        if self.root.state()!='zoomed':
            self._set_window_size(round(self.root.winfo_width()*self.scale/old_scale),round(self.root.winfo_height()*self.scale/old_scale))
        else:
            work_width,work_height = window_work_area(self.root)
            self.root.minsize(min(self.px(590),work_width),min(self.px(720),work_height))

    def _scale_layout(self,ratio):
        """Rescale explicit pixel spacing as the window moves between monitors."""
        def scaled(value):
            values = self.root.tk.splitlist(value) if isinstance(value,(str,tuple,list)) else (value,)
            result = tuple(round(float(v)*ratio) for v in values)
            return result[0] if len(result)==1 else result
        def visit(widget):
            for key in ('padding','wraplength','padx','pady'):
                if key in widget.keys():
                    value = widget.cget(key)
                    if str(value):
                        widget.configure(**{key:scaled(value)})
            manager = widget.winfo_manager()
            if manager in ('grid','pack'):
                info = widget.grid_info() if manager=='grid' else widget.pack_info()
                spacing = {key:scaled(info[key]) for key in ('padx','pady','ipadx','ipady') if key in info}
                if manager=='grid': widget.grid_configure(**spacing)
                else: widget.pack_configure(**spacing)
            for child in widget.winfo_children(): visit(child)
        for child in self.root.winfo_children(): visit(child)

    def _build(self):
        self.style = ttk.Style(self.root)
        if 'vista' in self.style.theme_names(): self.style.theme_use('vista')
        self.style.configure('TFrame',background=self.BG)
        self.style.configure('TLabel',background=self.BG,foreground=self.TEXT)
        self.style.configure('Muted.TLabel',foreground=self.MUTED)
        self.style.configure('Title.TLabel',font=('Segoe UI',18,'bold'))
        self.style.configure('Count.TLabel',font=('Segoe UI',16,'bold'))
        self.style.configure('Action.TButton',font=('Segoe UI',12),padding=(self.px(12),self.py(10)))
        self.style.configure('Help.TButton',font=('Segoe UI',10),padding=(self.px(2),0))
        self.style.configure('TCheckbutton',background=self.BG)
        main = self.main_frame = ttk.Frame(self.root,padding=(self.px(24),self.py(24)))
        main.pack(fill='both',expand=True)
        main.columnconfigure(0,weight=1)
        main.rowconfigure(9,weight=1)
        self.subtitle = ttk.Label(main,style='Title.TLabel')
        self.subtitle.grid(row=0,column=0,sticky='w')
        self.instructions = ttk.Label(main,style='Muted.TLabel',wraplength=self.px(570),justify='left')
        self.instructions.grid(row=1,column=0,sticky='ew',pady=(self.py(8),self.py(16)))
        self.status = ttk.Label(main,foreground=self.MUTED)
        self.status.grid(row=2,column=0,sticky='w',pady=(0,self.py(12)))
        self.count_label = ttk.Label(main,style='Count.TLabel')
        self.count_label.grid(row=3,column=0,sticky='w',pady=(0,self.py(14)))
        form = ttk.Frame(main)
        form.grid(row=4,column=0,sticky='ew')
        form.columnconfigure(1,weight=1)
        self.language_label = ttk.Label(form)
        self.language_label.grid(row=0,column=0,sticky='w',padx=(0,self.px(18)),pady=self.py(6))
        self.language_choice = ttk.Combobox(form,textvariable=self.game_language,state='readonly',values=tuple(GAME_LANGUAGES),width=23)
        self.language_choice.grid(row=0,column=1,sticky='ew',pady=self.py(6))
        self.language_choice.bind('<<ComboboxSelected>>',self._apply_language)
        self.target_label = ttk.Label(form)
        self.target_label.grid(row=1,column=0,sticky='w',pady=self.py(6))
        self.target_entry = ttk.Entry(form,textvariable=self.target,width=23)
        self.target_entry.grid(row=1,column=1,sticky='ew',pady=self.py(6))
        self.target_hint = ttk.Label(form,style='Muted.TLabel',wraplength=self.px(390))
        self.target_hint.grid(row=2,column=1,sticky='w',pady=(0,self.py(6)))
        self.shortcut_label = ttk.Label(form)
        self.shortcut_label.grid(row=3,column=0,sticky='w',pady=self.py(6))
        self.shortcut_entry = ttk.Entry(form,textvariable=self.shortcut_display,state='readonly',width=23)
        self.shortcut_entry.grid(row=3,column=1,sticky='ew',pady=self.py(6))
        self.shortcut_entry.bind('<Button-1>',self._begin_shortcut_capture)
        self.shortcut_entry.bind('<FocusOut>',self._end_shortcut_capture)
        self.shortcut_entry.bind('<KeyPress>',self._capture_shortcut)
        controls = ttk.Frame(main)
        controls.grid(row=5,column=0,sticky='ew',pady=(self.py(16),self.py(14)))
        controls.columnconfigure((0,1),weight=1,uniform='actions')
        self.start_button = ttk.Button(controls,command=self.start,style='Action.TButton')
        self.stop_button = ttk.Button(controls,command=self.stop,style='Action.TButton',state='disabled')
        self.start_button.grid(row=0,column=0,sticky='nsew',padx=(0,self.px(6)))
        self.stop_button.grid(row=0,column=1,sticky='nsew',padx=(self.px(6),0))
        developer = ttk.Frame(main)
        developer.grid(row=6,column=0,sticky='ew',pady=(0,self.py(14)))
        self.diagnostics_check = ttk.Checkbutton(developer,variable=self.diagnostics)
        self.diagnostics_check.pack(side='left')
        self.help_button = ttk.Button(developer,text='?',width=2,style='Help.TButton',command=self.show_developer_help)
        self.help_button.pack(side='left',padx=self.px(6))
        ttk.Separator(main).grid(row=7,column=0,sticky='ew')
        self.log_title = ttk.Label(main)
        self.log_title.grid(row=8,column=0,sticky='w',pady=(self.py(12),self.py(8)))
        log_frame = ttk.Frame(main)
        log_frame.grid(row=9,column=0,sticky='nsew')
        self.log = tk.Text(log_frame,wrap='word',state='disabled',font='TkFixedFont',height=8,bg='white',fg=self.TEXT,
                           relief='solid',bd=1,padx=self.px(10),pady=self.py(8))
        scroll = ttk.Scrollbar(log_frame,orient='vertical',command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y')
        self.log.pack(fill='both',expand=True)
        self.footer = ttk.Label(main,style='Muted.TLabel',wraplength=self.px(570))
        self.footer.grid(row=10,column=0,sticky='w',pady=(self.py(12),0))

    def _fit_content(self,event):
        """Compact vertical spacing on short/high-DPI screens, not the fonts."""
        if event.widget is not self.root: return
        spacing = .5 if event.height/self.scale<680 else 1.
        if spacing==self.spacing: return
        ratio,self.spacing = spacing/self.spacing,spacing
        def scaled(value):
            values = self.root.tk.splitlist(value) if isinstance(value,(str,tuple,list)) else (value,)
            result = tuple(round(float(v)*ratio) for v in values)
            return result[0] if len(result)==1 else result
        def visit(widget):
            if widget.winfo_manager()=='grid':
                info = widget.grid_info()
                widget.grid_configure(pady=scaled(info['pady']),ipady=scaled(info['ipady']))
            if 'pady' in widget.keys(): widget.configure(pady=scaled(widget.cget('pady')))
            for child in widget.winfo_children(): visit(child)
        visit(self.main_frame)
        self.main_frame.configure(padding=(self.px(24),self.py(24)))
        self.style.configure('Action.TButton',padding=(self.px(12),self.py(10)))

    def language_code(self): return GAME_LANGUAGES[self.game_language.get()]

    def _begin_shortcut_capture(self,_event=None):
        if not self.shortcut_entry.instate(['disabled']):
            self._shortcut_capturing = True
            self.shortcut_entry.focus_set()
            self.shortcut_display.set(tr(self.language_code(),'capture_shortcut'))
        return 'break'

    def _end_shortcut_capture(self,_event=None):
        self._shortcut_capturing = False
        self.shortcut_display.set(self.stop_key.get())

    def _cancel_shortcut_on_click(self,event):
        if event.widget is not self.shortcut_entry:
            self._end_shortcut_capture()

    def _capture_shortcut(self,event):
        if not self._shortcut_capturing or self.shortcut_entry.instate(['disabled']):
            return
        value = captured_hotkey(event.keysym,event.state,event.keycode)
        if value:
            self.stop_key.set(value)
            self._end_shortcut_capture()
        return 'break'  # No character insertion or default navigation actions.

    def _apply_language(self,_event=None):
        lang = self.language_code()
        self.root.title(f'Hololive Dreams — {tr(lang,"subtitle")} v{APP_VERSION}')
        for widget,key in ((self.subtitle,'subtitle'),(self.instructions,'instructions'),(self.language_label,'game_language'),
                           (self.target_label,'target_count'),(self.target_hint,'target_hint'),(self.shortcut_label,'stop_shortcut'),
                           (self.start_button,'start'),(self.stop_button,'stop'),(self.diagnostics_check,'developer_mode'),(self.log_title,'log')):
            widget.configure(text=tr(lang,key))
        self.footer.configure(text=f'v{APP_VERSION}')
        self._refresh_count()
        if not self.worker or not self.worker.is_alive():
            self._set_status(tr(lang,'error' if self.has_error else 'idle'),self.RED if self.has_error else self.MUTED)

    def _refresh_count(self):
        self.count_label.configure(text=tr(self.language_code(),'counter',count=self.counter.total))

    @staticmethod
    def bot_args(language='auto'):
        return argparse.Namespace(window_title='hololive-Dreams',language=language,fps=40.,lead=.20,deadband=.018,
            pulse_hz=7.,once=False,target_streak=0,target_catches=0,stop_hotkey='F9',max_seconds=0.,debug_dir=None,record=False)

    @staticmethod
    def diagnostic_base():
        return Path(os.environ.get('LOCALAPPDATA',str(Path.cwd())))/'HololiveFishingAuto'/'sessions'

    def show_developer_help(self):
        if self._developer_help_dialog and self._developer_help_dialog.winfo_exists():
            self._developer_help_dialog.lift()
            return self._developer_help_dialog
        lang = self.language_code()
        dialog = self._developer_help_dialog = tk.Toplevel(self.root)
        dialog.title(tr(lang,'developer_help_title'))
        dialog.transient(self.root)
        dialog.configure(bg=self.BG)
        dialog.resizable(False,False)
        try: dialog.iconbitmap(default=str(asset_path('fish-clear.ico')))
        except tk.TclError: pass
        content = ttk.Frame(dialog,name='content',padding=self.px(20))
        content.pack(fill='both',expand=True)
        marker = '__DIAGNOSTIC_FOLDER__'
        before,_,after = tr(lang,'developer_help',path=marker).partition(marker)
        ttk.Label(content,name='body',text=before.rstrip(),
                  wraplength=self.px(540),justify='left').pack(anchor='w')
        path_link = ttk.Label(content,name='diagnostic_link',text=str(self.diagnostic_base()),
                              foreground=self.CYAN,font=('Segoe UI',11,'underline'),
                              cursor='hand2',takefocus=True,wraplength=self.px(540),justify='left')
        path_link.pack(anchor='w',pady=(self.px(4),0))
        path_link.bind('<Button-1>',self.open_diagnostics)
        path_link.bind('<Return>',self.open_diagnostics)
        path_link.bind('<space>',self.open_diagnostics)
        ttk.Label(content,name='details',text=after.strip(),wraplength=self.px(540),
                  justify='left').pack(anchor='w',pady=(self.px(12),0))
        ttk.Label(content,name='project_label',text=tr(lang,'project_address')).pack(anchor='w',pady=(self.px(16),self.px(4)))
        link = ttk.Label(content,name='project_link',text=PROJECT_URL,foreground=self.CYAN,
                         font=('Segoe UI',11,'underline'),cursor='hand2',takefocus=True,
                         wraplength=self.px(540),justify='left')
        link.pack(anchor='w')
        link.bind('<Button-1>',self.open_project)
        link.bind('<Return>',self.open_project)
        link.bind('<space>',self.open_project)
        close = ttk.Button(content,text=tr(lang,'close_help'),command=dialog.destroy)
        close.pack(anchor='e',pady=(self.px(20),0))
        dialog.bind('<Escape>',lambda _event:dialog.destroy())
        dialog.grab_set()
        close.focus_set()
        return dialog

    @staticmethod
    def open_project(_event=None):
        webbrowser.open_new_tab(PROJECT_URL)
        return 'break'

    def open_diagnostics(self,_event=None):
        try:
            directory = self.diagnostic_base().resolve()
            # Also make the link usable before the first diagnostic run.
            directory.mkdir(parents=True,exist_ok=True)
            os.startfile(str(directory))
        except OSError as exc:
            parent = self._developer_help_dialog or self.root
            messagebox.showerror(tr(self.language_code(),'error'),str(exc),parent=parent)
        return 'break'

    def _append_log(self,message):
        self.log.configure(state='normal')
        self.log.insert('end',message+'\n')
        if int(self.log.index('end-1c').split('.')[0])>1000: self.log.delete('1.0','101.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def _set_status(self,text,color): self.status.configure(text=text,foreground=color)

    def start(self):
        if self.worker and self.worker.is_alive(): return
        lang = self.language_code()
        try:
            target = int(self.target.get())
            if target<0: raise ValueError('Negative target')
            hotkey = self.stop_key.get().strip()
            parse_stop_hotkey(hotkey)
        except ValueError:
            messagebox.showerror(tr(lang,'error'),tr(lang,'invalid_settings'),parent=self.root)
            return
        self.counter.begin_run()
        self._refresh_count()
        self.stop_event.clear()
        self.has_error = False
        self.session_args = self.bot_args(lang)
        self.session_args.target_catches = target
        self.session_args.stop_hotkey = hotkey
        self._set_controls(True)
        self._set_status(tr(lang,'connecting'),self.CYAN)
        self._append_log(tr(lang,'started',language=self.game_language.get()))
        if self.diagnostics.get():
            directory = self.diagnostic_base()/time.strftime('%Y%m%d-%H%M%S')
            self.session_args.debug_dir = str(directory)
            self._append_log(tr(lang,'diagnostic_path',path=directory))
        self.worker = threading.Thread(target=self._run_bot,name='fishing-bot',daemon=True)
        self.worker.start()

    def _set_controls(self,running):
        self._end_shortcut_capture()
        self.start_button.configure(state='disabled' if running else 'normal')
        self.stop_button.configure(state='normal' if running else 'disabled')
        self.language_choice.configure(state='disabled' if running else 'readonly')
        self.shortcut_entry.configure(state='disabled' if running else 'readonly')
        for widget in (self.target_entry,self.diagnostics_check):
            widget.configure(state='disabled' if running else 'normal')

    def _run_bot(self):
        try:
            run(self.session_args,stop_event=self.stop_event,status_callback=lambda value:self.messages.put(('log',value)),
                progress_callback=lambda value:self.messages.put(('progress',value)))
        except Exception as exc: self.messages.put(('error',str(exc)))
        finally: self.messages.put(('done',None))

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.stop_button.configure(state='disabled')
            self._set_status(tr(self.session_args.language,'stopping'),self.MUTED)

    def _poll(self):
        try:
            while True:
                kind,value = self.messages.get_nowait()
                lang = self.session_args.language
                if kind=='progress':
                    self.counter.update(value['catches'])
                    self._refresh_count()
                elif kind=='log' and value:
                    self._append_log(value)
                    prefix = tr(lang,'state_prefix')
                    if value.startswith(prefix): self._set_status(value[len(prefix):],self.GREEN)
                elif kind=='error':
                    self.has_error = True
                    self._append_log(f'{tr(lang,"error")}: {value}')
                    self._set_status(tr(lang,'error'),self.RED)
                    if not self._closing: messagebox.showerror(tr(lang,'error_title'),value,parent=self.root)
                elif kind=='done':
                    self._set_controls(False)
                    if not self.has_error: self._set_status(tr(lang,'stopped'),self.MUTED)
        except queue.Empty: pass
        if not self._closing: self.root.after(100,self._poll)

    def close(self):
        self._closing = True
        self.stop_event.set()
        self.root.after(150,self._finish_close)

    def _finish_close(self):
        if self.worker and self.worker.is_alive(): self.root.after(100,self._finish_close)
        else: self.root.destroy()


def main():
    enable_dpi_awareness()
    # New icon identity avoids reusing the old pinned/taskbar icon identity.
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('HololiveFishingAuto.Desktop.ClearIcon')
    except (AttributeError,OSError): pass
    root = tk.Tk()
    FishingApp(root)
    root.mainloop()


if __name__=='__main__': main()
