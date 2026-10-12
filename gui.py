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
from PIL import Image, ImageTk
from global_hotkey import GlobalHotkey
from startup_trace import startup_log, remove_legacy_startup_logs
from auto_fishing import enable_dpi_awareness, run
from app_locale import GAME_LANGUAGES, text as tr
from app_settings import FishingCounter, parse_stop_hotkey, captured_hotkey, hotkeys_conflict
from fluent_theme import FluentTheme, BG, TEXT, MUTED, ACCENT, SURFACE

APP_VERSION = '1.1.1'
APP_BUILD = '1.1.1'
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
    BG,TEXT,MUTED = BG,TEXT,MUTED
    CYAN,GREEN,RED = '#1B6798','#187b38','#b42318'

    def __init__(self,root):
        self.root = root
        root.configure(bg=self.BG)
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.dpi = window_dpi(root)
        self.scale = self.dpi/96
        self.spacing = 1.
        root.tk.call('tk','scaling',self.dpi/72)
        self._configure_fonts()
        self._set_window_size(self.px(450),self.px(800))
        self.messages = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None
        self._closing = self.has_error = False
        self.counter = FishingCounter()
        self.game_language = tk.StringVar(value='繁體中文')
        self.target = tk.StringVar(value='0')
        self.target_mode = tk.StringVar(value='unlimited')
        self.target_amount = tk.StringVar(value='1')
        self._target_syncing = False
        self._controls_running = False
        self.start_key = tk.StringVar(value='F8')
        self.start_shortcut_display = tk.StringVar(value='F8')
        self._launch_lock = threading.Lock()
        self._run_id = 0
        self._display_run_id = 0
        self._start_snapshot = None
        self._hotkey_enabled = True
        self._capture_target = 'stop'
        self.stop_key = tk.StringVar(value='F9')
        self.shortcut_display = tk.StringVar(value='F9')
        self._shortcut_capturing = False
        self._developer_help_dialog = None
        self.diagnostics = tk.BooleanVar(value=False)
        self.session_args = self.bot_args('zh-TW')
        self._build()
        self._apply_language()
        try: root.iconbitmap(default=str(asset_path('fishing-hook.ico')))
        except tk.TclError: pass
        root.bind('<Configure>',self._dpi_changed,add='+')
        root.bind('<Configure>',self._fit_content,add='+')
        root.bind('<Button-1>',self._cancel_shortcut_on_click,add='+')
        self._hotkey = GlobalHotkey(self._hotkey_start, self._hotkey_report)
        self.target.trace_add('write',self._target_value_changed)
        for variable in (self.target_mode,self.target_amount):
            variable.trace_add('write',self._target_controls_changed)
        for variable in (self.game_language,self.target,self.start_key,self.stop_key,self.diagnostics):
            variable.trace_add('write',self._snapshot_settings)
        self._snapshot_settings()
        self._hotkey.start()
        root.bind('<Destroy>',self._destroy_listener,add='+')
        root.after(100,self._poll)

    def px(self,value): return round(value*self.scale)
    def py(self,value): return round(value*self.scale*self.spacing)

    def _set_window_size(self,width,height):
        work_width,work_height = window_work_area(self.root)
        available_width = max(1,work_width-self.px(40))
        available_height = max(1,work_height-self.px(40))
        self.root.minsize(min(self.px(400),available_width),min(self.px(640),available_height))
        content_height = min(height,available_height)
        if not hasattr(self,'main_frame'):
            self.spacing = .5 if content_height/self.scale<680 else 1.
        self.root.geometry(f'{min(width,available_width)}x{content_height}')

    def _configure_fonts(self):
        for name in ('TkDefaultFont','TkTextFont','TkMenuFont','TkHeadingFont'):
            font.nametofont(name).configure(family='Segoe UI',size=-round(10*self.dpi/72))
        font.nametofont('TkFixedFont').configure(family='Consolas',size=-round(10*self.dpi/72))
        for name,points in (('FishingTitleFont',18),('FishingCountFont',20)):
            if name not in font.names(self.root):
                setattr(self,'_'+name,font.Font(self.root,name=name,family='Segoe UI',weight='bold'))
            font.nametofont(name).configure(size=-round(points*self.dpi/72))

    def _dpi_changed(self,event):
        if event.widget is not self.root: return
        dpi = window_dpi(self.root)
        if dpi==self.dpi: return
        old_scale = self.scale
        self.dpi,self.scale = dpi,dpi/96
        self.root.tk.call('tk','scaling',dpi/72)
        self._configure_fonts()
        self._scale_layout(self.scale/old_scale)
        self.style.configure('Title.TLabel',font='FishingTitleFont')
        self.style.configure('Count.TLabel',font='FishingCountFont')
        self._activate_theme()
        if self.root.state()!='zoomed':
            self._set_window_size(round(self.root.winfo_width()*self.scale/old_scale),round(self.root.winfo_height()*self.scale/old_scale))
        else:
            work_width,work_height = window_work_area(self.root)
            self.root.minsize(min(self.px(400),work_width),min(self.px(640),work_height))

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

    def _activate_theme(self):
        key = round(self.scale*96)
        if key not in self._themes:
            self._themes[key] = FluentTheme(self.root,self.scale)
        self.theme = self._themes[key]
        self.theme.activate()
        self.style = self.theme.style
        if key not in self._logo_images:
            with Image.open(asset_path('snowsea-angel-thumb.png')) as source:
                artwork=source.convert('RGBA')
                artwork=artwork.crop(artwork.getchannel('A').getbbox())
                artwork.thumbnail((self.px(72),self.px(50)),Image.Resampling.LANCZOS)
                self._logo_images[key]=ImageTk.PhotoImage(artwork,master=self.root)
        self.game_logo.configure(image=self._logo_images[key])
        for button,icons in ((self.start_button,self.theme.play_icons),(self.stop_button,self.theme.stop_icons)):
            button.configure(image=(icons['normal'],'disabled',icons['disabled']),compound='left')
        self.help_button.configure(image=self.theme.help_icon)
        for name in ('Primary','Secondary'):
            self.style.configure(name+'.TButton',padding=(self.px(12),self.py(10)))

    def _build(self):
        self._themes = {self.dpi:FluentTheme(self.root,self.scale)}
        self.theme = self._themes[self.dpi]
        self.style = self.theme.style
        self._logo_images = {}
        main = self.main_frame = ttk.Frame(self.root,padding=(self.px(24),self.py(24)))
        main.pack(fill='both',expand=True)
        main.columnconfigure(0,weight=1)
        main.rowconfigure(7,weight=1)
        heading=ttk.Frame(main)
        heading.grid(row=0,column=0,sticky='ew')
        heading.columnconfigure(1,weight=1)
        self.game_logo=ttk.Label(heading)
        self.game_logo.grid(row=0,column=0,padx=(0,self.px(12)))
        self.subtitle = ttk.Label(heading,style='Title.TLabel',wraplength=self.px(318),justify='left')
        self.subtitle.grid(row=0,column=1,sticky='ew')
        self.instructions = ttk.Label(main,style='Muted.TLabel',wraplength=self.px(552),justify='left')
        self.instructions.grid(row=1,column=0,sticky='ew',pady=(self.py(8),self.py(16)))
        summary = self.summary_card = ttk.Frame(main,style='Card.TFrame',padding=self.px(16))
        summary.grid(row=3,column=0,sticky='ew',pady=(0,self.py(12)))
        summary.columnconfigure(0,weight=1)
        self.status = ttk.Label(main,style='Muted.TLabel',wraplength=self.px(402))
        self.status.grid(row=2,column=0,sticky='ew',pady=(0,self.py(12)))
        self.count_label = ttk.Label(summary,style='Count.TLabel',wraplength=self.px(520))
        self.count_label.grid(row=0,column=0,sticky='ew')
        form = self.settings_card = ttk.Frame(main,style='Card.TFrame',padding=self.px(16))
        form.grid(row=4,column=0,sticky='ew',pady=(0,self.py(12)))
        form.columnconfigure(1,weight=1)
        self.language_label = ttk.Label(form,style='Card.TLabel')
        self.language_label.grid(row=0,column=0,sticky='w',padx=(0,self.px(18)),pady=self.py(6))
        self.language_choice = ttk.Combobox(form,textvariable=self.game_language,state='readonly',values=tuple(GAME_LANGUAGES),width=12)
        self.language_choice.grid(row=0,column=1,sticky='ew',pady=self.py(6))
        self.language_choice.bind('<<ComboboxSelected>>',self._apply_language)
        self.target_label = ttk.Label(form,style='Card.TLabel')
        self.target_label.grid(row=1,column=0,sticky='w',padx=(0,self.px(18)),pady=self.py(6))
        target_options=ttk.Frame(form,style='Surface.TFrame')
        target_options.grid(row=1,column=1,sticky='ew',pady=self.py(6))
        target_options.columnconfigure(2,weight=1)
        self.unlimited_choice=ttk.Radiobutton(target_options,variable=self.target_mode,value='unlimited')
        self.unlimited_choice.grid(row=0,column=0,sticky='w',padx=(0,self.px(10)))
        self.amount_choice=ttk.Radiobutton(target_options,variable=self.target_mode,value='count',text='')
        self.amount_choice.grid(row=0,column=1,sticky='w')
        self.target_entry = ttk.Entry(target_options,textvariable=self.target_amount,width=6,state='disabled')
        self.target_entry.grid(row=0,column=2,sticky='ew')
        self.start_shortcut_label = ttk.Label(form,style='Card.TLabel')
        self.start_shortcut_label.grid(row=2,column=0,sticky='w',padx=(0,self.px(18)),pady=self.py(6))
        self.start_shortcut_entry = ttk.Entry(form,textvariable=self.start_shortcut_display,state='readonly',width=16)
        self.start_shortcut_entry.grid(row=2,column=1,sticky='ew',pady=self.py(6))
        self.start_shortcut_entry.bind('<Button-1>',lambda event:self._begin_shortcut_capture(event,'start'))
        self.start_shortcut_entry.bind('<FocusOut>',self._end_shortcut_capture)
        self.start_shortcut_entry.bind('<KeyPress>',self._capture_shortcut)
        self.shortcut_label = ttk.Label(form,style='Card.TLabel')
        self.shortcut_label.grid(row=3,column=0,sticky='w',padx=(0,self.px(18)),pady=self.py(6))
        self.shortcut_entry = ttk.Entry(form,textvariable=self.shortcut_display,state='readonly',width=16)
        self.shortcut_entry.grid(row=3,column=1,sticky='ew',pady=self.py(6))
        self.shortcut_entry.bind('<Button-1>',self._begin_shortcut_capture)
        self.shortcut_entry.bind('<FocusOut>',self._end_shortcut_capture)
        self.shortcut_entry.bind('<KeyPress>',self._capture_shortcut)
        controls = ttk.Frame(main)
        controls.grid(row=5,column=0,sticky='ew',pady=(0,self.py(12)))
        controls.columnconfigure((0,1),weight=1,uniform='actions')
        self.start_button = ttk.Button(controls,command=self.start,style='Primary.TButton')
        self.stop_button = ttk.Button(controls,command=self.stop,style='Secondary.TButton',state='disabled')
        self.start_button.grid(row=0,column=0,sticky='nsew',padx=(0,self.px(6)))
        self.stop_button.grid(row=0,column=1,sticky='nsew',padx=(self.px(6),0))
        developer = ttk.Frame(main)
        developer.grid(row=6,column=0,sticky='ew',pady=(0,self.py(12)))
        self.diagnostics_check = ttk.Checkbutton(developer,variable=self.diagnostics)
        self.diagnostics_check.pack(side='left')
        self.help_button = ttk.Button(developer,width=2,style='Help.TButton',command=self.show_developer_help)
        self.help_button.pack(side='left',padx=self.px(6))
        activity = self.log_card = ttk.Frame(main,style='Card.TFrame',padding=self.px(16))
        activity.grid(row=7,column=0,sticky='nsew')
        activity.columnconfigure(0,weight=1)
        activity.rowconfigure(1,weight=1)
        self.log_title = ttk.Label(activity,style='CardMuted.TLabel')
        self.log_title.grid(row=0,column=0,sticky='w',pady=(0,self.py(8)))
        log_frame = ttk.Frame(activity,style='Surface.TFrame')
        log_frame.grid(row=1,column=0,sticky='nsew')
        self.log = tk.Text(log_frame,wrap='word',state='disabled',font='TkFixedFont',height=1,width=1,bg=SURFACE,fg=self.TEXT,
                           relief='flat',bd=0,highlightthickness=0,padx=0,pady=self.py(2),spacing3=self.py(3))
        scroll = ttk.Scrollbar(log_frame,orient='vertical',command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y',padx=(self.px(8),0))
        self.log.pack(fill='both',expand=True)
        self.footer = ttk.Label(main,style='Muted.TLabel',wraplength=self.px(552))
        self.footer.grid(row=8,column=0,sticky='w',pady=(self.py(12),0))
        self._wrap_width = None
        self._activate_theme()

    def _fit_content(self,event):
        """Only update spacing at a threshold and wrapping when width changes."""
        if event.widget is not self.root: return
        spacing = .5 if event.height/self.scale<680 else 1.
        if spacing != self.spacing:
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
            for name in ('Primary','Secondary'):
                self.style.configure(name+'.TButton',padding=(self.px(12),self.py(10)))
        width = max(self.px(200),event.width-self.px(48))
        key = (width,self.dpi)
        if key==self._wrap_width: return
        self._wrap_width = key
        for label in (self.instructions,self.footer,self.status): label.configure(wraplength=width)
        self.subtitle.configure(wraplength=max(self.px(120),width-self.px(84)))
        self.count_label.configure(wraplength=max(1,width-self.px(32)))

    def _center_dialog(self,dialog):
        dialog.update_idletasks()
        width,height = dialog.winfo_reqwidth(),dialog.winfo_reqheight()
        monitor = win32api.GetMonitorInfo(win32api.MonitorFromWindow(self.root.winfo_id(),2))['Work']
        left,top,right,bottom = monitor
        x = self.root.winfo_rootx()+(self.root.winfo_width()-width)//2
        y = self.root.winfo_rooty()+(self.root.winfo_height()-height)//2
        x = min(max(x,left),max(left,right-width))
        y = min(max(y,top),max(top,bottom-height))
        dialog.geometry(f'{width}x{height}{x:+}{y:+}')
        dialog.deiconify()

    def language_code(self): return GAME_LANGUAGES[self.game_language.get()]

    def _update_target_controls(self):
        self.target_entry.configure(state='disabled' if self._controls_running or self.target_mode.get()=='unlimited' else 'normal')
        for widget in (self.unlimited_choice,self.amount_choice):
            widget.configure(state='disabled' if self._controls_running else 'normal')

    def _target_controls_changed(self,*_):
        if self._target_syncing: return
        self._target_syncing=True
        try:
            value='0' if self.target_mode.get()=='unlimited' else self.target_amount.get()
            if self.target_mode.get()=='count':
                try:
                    if int(value)<=0: value='-1'
                except ValueError:
                    pass
            self.target.set(value)
        finally:
            self._target_syncing=False
        self._update_target_controls()
        self._snapshot_settings()

    def _target_value_changed(self,*_):
        # Keep the legacy effective target (0 = unlimited) for the worker and
        # immutable hotkey snapshot; selecting a limit never changes game logic.
        if self._target_syncing: return
        self._target_syncing=True
        try:
            self.target_mode.set('unlimited' if self.target.get()=='0' else 'count')
            if self.target.get()!='0': self.target_amount.set(self.target.get())
        finally:
            self._target_syncing=False
        self._update_target_controls()
        self._snapshot_settings()

    def _begin_shortcut_capture(self,_event=None,target='stop'):
        entry = self.start_shortcut_entry if target=='start' else self.shortcut_entry
        if not entry.instate(['disabled']):
            self._end_shortcut_capture()
            self._capture_target = target
            self._shortcut_capturing = True
            self._hotkey.configure(enabled=False)
            entry.focus_set()
            display = self.start_shortcut_display if target=='start' else self.shortcut_display
            display.set(tr(self.language_code(),'capture_shortcut'))
        return 'break'

    def _end_shortcut_capture(self,_event=None):
        self._shortcut_capturing = False
        self.shortcut_display.set(self.stop_key.get())
        self.start_shortcut_display.set(self.start_key.get())

    def _cancel_shortcut_on_click(self,event):
        if event.widget not in (self.shortcut_entry,self.start_shortcut_entry):
            self._end_shortcut_capture()

    def _capture_shortcut(self,event):
        entry = self.start_shortcut_entry if self._capture_target=='start' else self.shortcut_entry
        if not self._shortcut_capturing or entry.instate(['disabled']):
            return
        value = captured_hotkey(event.keysym,event.state,event.keycode)
        if value:
            variable = self.start_key if self._capture_target=='start' else self.stop_key
            other = self.stop_key if self._capture_target=='start' else self.start_key
            self._hotkey.configure(enabled=False)
            self._end_shortcut_capture()
            if hotkeys_conflict(value,other.get()):
                messagebox.showerror(tr(self.language_code(),'error'),tr(self.language_code(),'shortcut_conflict'),parent=self.root)
            else:
                variable.set(value)
                self._end_shortcut_capture()
        return 'break'

    def _snapshot_settings(self,*_):
        # Only the GUI thread reads Tk variables. The listener reads this
        # immutable snapshot and can launch while Tk is hidden or busy.
        self._start_snapshot = (self.language_code(),self.game_language.get(),
                                self.target.get(),self.start_key.get(),self.stop_key.get(),self.diagnostics.get())
        self._hotkey.configure(value=self.start_key.get())

    def _hotkey_report(self,value,registered,error):
        startup_log(f'{APP_BUILD} hotkey {value} registered={registered} error={error}')
        self.messages.put(('hotkey_status',(value,registered,error)))

    def _poll_start_hotkey(self):
        self._hotkey_enabled = (not self._closing and not self._shortcut_capturing
                                and self.root.grab_current() is None)
        self._hotkey.configure(enabled=self._hotkey_enabled)

    def _hotkey_start(self):
        # No Tk calls: Windows message -> snapshot -> fishing worker.
        if self._closing or self._shortcut_capturing or not self._hotkey_enabled:
            return
        startup_log(f'{APP_BUILD} global start received')
        try:
            self._launch(self._start_snapshot,'hotkey')
        except Exception as exc:
            startup_log(f'{APP_BUILD} global launch failed: {exc}')
            self.messages.put(('settings_error',str(exc)))

    def _destroy_listener(self,event):
        if event.widget is self.root:
            self._hotkey.close()

    def _apply_language(self,_event=None):
        lang = self.language_code()
        self.root.title(f'Hololive Dreams — {tr(lang,"subtitle")}')
        for widget,key in ((self.subtitle,'subtitle'),(self.instructions,'instructions'),(self.language_label,'game_language'),
                           (self.target_label,'target_count'),(self.unlimited_choice,'unlimited'),(self.shortcut_label,'stop_shortcut'),(self.start_shortcut_label,'start_shortcut'),
                           (self.start_button,'start'),(self.stop_button,'stop'),(self.diagnostics_check,'developer_mode'),(self.log_title,'log')):
            widget.configure(text=tr(lang,key))
        self.footer.configure(text=f'v{APP_VERSION}')
        self._refresh_count()
        if not self.worker or not self.worker.is_alive():
            self._set_status(tr(lang,'error' if self.has_error else 'idle'),self.RED if self.has_error else self.CYAN)

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
        dialog.withdraw()
        try: dialog.iconbitmap(default=str(asset_path('fishing-hook.ico')))
        except tk.TclError: pass
        panel = ttk.Frame(dialog,name='panel',padding=self.px(20))
        panel.pack(fill='both',expand=True)
        content = ttk.Frame(panel,name='content',style='Card.TFrame',padding=self.px(16))
        content.pack(fill='x',pady=(0,self.px(12)))
        wrap=min(self.px(420),window_work_area(self.root)[0]-self.px(80))
        ttk.Label(content,text=tr(lang,'developer_mode'),style='Card.TLabel',
                  font=('Segoe UI',-round(11*self.dpi/72),'bold')).pack(anchor='w',pady=(0,self.px(8)))
        marker = '__DIAGNOSTIC_FOLDER__'
        before,_,after = tr(lang,'developer_help',path=marker).partition(marker)
        ttk.Label(content,name='body',text=before.rstrip(),style='CardMuted.TLabel',
                  wraplength=wrap,justify='left').pack(anchor='w')
        path_link = ttk.Label(content,name='diagnostic_link',text=str(self.diagnostic_base()),style='Card.TLabel',
                              foreground=self.CYAN,font=('Segoe UI',-round(10*self.dpi/72),'underline'),
                              cursor='hand2',takefocus=True,wraplength=wrap,justify='left')
        path_link.pack(anchor='w',pady=(self.px(4),0))
        path_link.bind('<Button-1>',self.open_diagnostics)
        path_link.bind('<Return>',self.open_diagnostics)
        path_link.bind('<space>',self.open_diagnostics)
        ttk.Label(content,name='details',text=after.strip(),style='CardMuted.TLabel',wraplength=wrap,
                  justify='left').pack(anchor='w',pady=(self.px(12),0))
        project = ttk.Frame(panel,name='project',style='Card.TFrame',padding=self.px(16))
        project.pack(fill='x',pady=(0,self.px(12)))
        ttk.Label(project,name='project_label',text=tr(lang,'project_address'),style='Card.TLabel',
                  font=('Segoe UI',-round(11*self.dpi/72),'bold')).pack(anchor='w',pady=(0,self.px(8)))
        link = ttk.Label(project,name='project_link',text=PROJECT_URL,style='Card.TLabel',foreground=self.CYAN,
                         font=('Segoe UI',-round(10*self.dpi/72),'underline'),cursor='hand2',takefocus=True,
                         wraplength=wrap,justify='left')
        link.pack(anchor='w')
        link.bind('<Button-1>',self.open_project)
        link.bind('<Return>',self.open_project)
        link.bind('<space>',self.open_project)
        close = ttk.Button(panel,text=tr(lang,'close_help'),command=dialog.destroy,style='Primary.TButton')
        close.pack(anchor='e')
        dialog.bind('<Escape>',lambda _event:dialog.destroy())
        self._center_dialog(dialog)
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
        self._snapshot_settings()
        try:
            info = self._launch(self._start_snapshot,'button')
        except ValueError as exc:
            messagebox.showerror(tr(self.language_code(),'error'),str(exc),parent=self.root)
            return
        if info:
            self._show_start(info)

    def _launch(self,snapshot,source):
        lang,language_name,target_text,start_key,stop_key,diagnostics = snapshot
        try:
            target = int(target_text)
            if target < 0: raise ValueError()
            parse_stop_hotkey(start_key)
            parse_stop_hotkey(stop_key)
        except ValueError:
            raise ValueError(tr(lang,'invalid_settings')) from None
        if hotkeys_conflict(start_key,stop_key):
            raise ValueError(tr(lang,'shortcut_conflict'))
        with self._launch_lock:
            if self._closing or (self.worker and self.worker.is_alive()):
                return None
            self._run_id += 1
            run_id = self._run_id
            args = self.bot_args(lang)
            args.target_catches, args.stop_hotkey = target,stop_key.strip()
            args.start_source = source
            if diagnostics:
                args.debug_dir = str(self.diagnostic_base()/(time.strftime('%Y-%m-%d_%H-%M-%S')+f'-{time.time_ns()%1000000000:09d}'))
            self.session_args = args
            self.stop_event.clear()
            info = (run_id,args,language_name,source)
            self.messages.put((run_id,'starting',info))
            startup_log(f'{APP_BUILD} launch run={run_id} source={source} start={start_key} stop={stop_key}', args.debug_dir)
            self.worker = threading.Thread(target=self._run_bot,args=(args,run_id),name='fishing-bot',daemon=True)
            try:
                self.worker.start()
            except Exception as exc:
                startup_log(f'{APP_BUILD} cannot start worker: {exc}', args.debug_dir)
                self.messages.put((run_id,'error',str(exc)))
                self.messages.put((run_id,'done',None))
            return info

    def _show_start(self,info):
        run_id,args,language_name,source = info
        if self._display_run_id == run_id:
            return
        self._display_run_id = run_id
        self.counter.begin_run()
        self._refresh_count()
        self.has_error = False
        self._set_controls(True)
        self._set_status(tr(args.language,'connecting'),self.CYAN)
        self._append_log(tr(args.language,'started',language=language_name))
        self._append_log(tr(args.language,'start_source',source=tr(args.language,'source_'+source),build=APP_BUILD))
        if args.debug_dir:
            self._append_log(tr(args.language,'diagnostic_path',path=args.debug_dir))

    def _set_controls(self,running):
        self._controls_running=running
        self._end_shortcut_capture()
        self.start_button.configure(state='disabled' if running else 'normal')
        self.stop_button.configure(state='normal' if running else 'disabled')
        self.language_choice.configure(state='disabled' if running else 'readonly')
        self.shortcut_entry.configure(state='disabled' if running else 'readonly')
        self.start_shortcut_entry.configure(state='disabled' if running else 'readonly')
        for widget in (self.target_entry,self.diagnostics_check):
            widget.configure(state='disabled' if running else 'normal')
        self._update_target_controls()

    def _run_bot(self,args,run_id):
        try:
            run(args,stop_event=self.stop_event,status_callback=lambda value:self.messages.put((run_id,'log',value)),
                progress_callback=lambda value:self.messages.put((run_id,'progress',value)))
        except Exception as exc:
            startup_log(f'{APP_BUILD} run={run_id} failed: {exc}', args.debug_dir)
            self.messages.put((run_id,'error',str(exc)))
        finally:
            self.messages.put((run_id,'done',None))
            startup_log(f'{APP_BUILD} run={run_id} finished', args.debug_dir)
            if args.debug_dir:
                folder = Path(args.debug_dir)
                if ((folder/'startup.log').is_file() and not any(folder.glob('diagnostics-*.zip'))
                        and not (folder/'trace.csv').exists() and not (folder/'diagnostics.json').exists()):
                    try:
                        from diagnostics import DiagnosticWriter
                        DiagnosticWriter(folder).close()
                    except Exception as exc:
                        self.messages.put((run_id,'log',str(exc)))

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.stop_button.configure(state='disabled')
            self._set_status(tr(self.session_args.language,'stopping'),self.MUTED)

    def _poll(self):
        self._poll_start_hotkey()
        try:
            while True:
                item = self.messages.get_nowait()
                if len(item)==3:
                    run_id,kind,value = item
                    if run_id != self._run_id:
                        continue
                else:
                    kind,value = item
                lang = self.session_args.language
                if kind=='starting':
                    self._show_start(value)
                elif kind=='hotkey_status':
                    key,registered,error = value
                    self._append_log(tr(self.language_code(),'hotkey_ready' if registered else 'hotkey_unavailable',hotkey=key,error=error))
                elif kind=='settings_error':
                    messagebox.showerror(tr(lang,'error'),value,parent=self.root)
                elif kind=='progress':
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
        self._hotkey_enabled = False
        self._hotkey.close()
        self.stop_event.set()
        self.root.after(150,self._finish_close)

    def _finish_close(self):
        if self.worker and self.worker.is_alive(): self.root.after(100,self._finish_close)
        else: self.root.destroy()


def main():
    remove_legacy_startup_logs()
    enable_dpi_awareness()
    # New icon identity avoids reusing the old pinned/taskbar icon identity.
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('HololiveFishingAuto.Desktop.HookIcon')
    except (AttributeError,OSError): pass
    root = tk.Tk()
    FishingApp(root)
    root.mainloop()


if __name__=='__main__': main()
