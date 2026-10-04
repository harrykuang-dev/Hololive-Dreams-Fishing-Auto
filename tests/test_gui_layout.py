"""Inspect Tk widget geometry only; never starts the game/input runtime."""
import unittest
from unittest.mock import patch
import tkinter as tk
from types import SimpleNamespace
from gui import FishingApp, PROJECT_URL
from app_locale import GAME_LANGUAGES, text
from tkinter import ttk

class LayoutTests(unittest.TestCase):
    def setUp(self):
        # Geometry tests never register or consume real keyboard shortcuts.
        self.listener_patch=patch('gui.GlobalHotkey')
        self.listener=self.listener_patch.start()
        self.addCleanup(self.listener_patch.stop)
        self.trace_patch=patch('gui.startup_log')
        self.trace_patch.start()
        self.addCleanup(self.trace_patch.stop)

    def test_buttons_match_and_controls_fit_at_multiple_dpis(self):
        for dpi in (96,120,144,192):
            root=tk.Tk()
            # A simulated 200% monitor needs more physical pixels than the
            # hosted runner's 1024x768 desktop. Validate scaling against an
            # explicit 4K work area, not the unrelated host's resolution.
            root.maxsize(3840,2160)
            try:
                with patch('gui.window_dpi',return_value=dpi), patch('gui.window_work_area',return_value=(3840,2160)):
                    app=FishingApp(root)
                    root.update()
                    for language in GAME_LANGUAGES:
                        app.game_language.set(language)
                        app._apply_language()
                        root.update()
                        self.assertEqual(app.language_label.cget('text'),text(app.language_code(),'game_language'))
                        self.assertIsInstance(app.target_entry,ttk.Entry)
                        self.assertNotIsInstance(app.target_entry,ttk.Spinbox)
                        self.assertLess(app.help_button.winfo_height(),app.start_button.winfo_height())
                        self.assertEqual(app.start_button.winfo_height(),app.stop_button.winfo_height())
                        self.assertGreater(app.log.winfo_height(),40,(dpi,language,root.winfo_height(),root.winfo_reqheight()))
                        self.assertLess(app.footer.winfo_rooty()-app.main_frame.winfo_rooty(),app.main_frame.winfo_height())
                        self.assertLessEqual(app.footer.winfo_rooty()+app.footer.winfo_height(),
                                             root.winfo_rooty()+root.winfo_height())
                    app.messages.put(('progress',{'catches':2}))
                    app._poll()
                    self.assertEqual(app.counter.total,2)
                    self.assertIn('2',app.count_label.cget('text'))
                    if dpi==96:
                        # Move to a higher-DPI monitor, including pixel spacing.
                        old_wrap = int(app.instructions.cget('wraplength'))
                        with patch('gui.window_dpi',return_value=144):
                            app._dpi_changed(SimpleNamespace(widget=root))
                            root.update()
                            self.assertEqual(int(app.instructions.cget('wraplength')),round(old_wrap*1.5))
                            self.assertEqual(app.start_button.winfo_height(),app.stop_button.winfo_height())
            finally:
                app._closing=True
                for callback in root.tk.splitlist(root.tk.call('after','info')):
                    root.after_cancel(callback)
                root.destroy()

    def test_shortcut_capture_replaces_key_and_cannot_edit_while_running(self):
        root=tk.Tk()
        app=FishingApp(root)
        try:
            self.assertEqual(app.stop_key.get(),'F9')
            self.assertTrue(app.shortcut_entry.instate(['readonly']))
            self.assertFalse(app.shortcut_entry.bind('<FocusIn>'))
            self.assertTrue(app.shortcut_entry.bind('<Button-1>'))
            app._begin_shortcut_capture()
            self.assertEqual(app.shortcut_display.get(),text('zh-TW','capture_shortcut'))
            modifier=SimpleNamespace(keysym='Control_L',state=4,keycode=0x11)
            key=SimpleNamespace(keysym='q',state=0x20004,keycode=0x51)
            self.assertEqual(app._capture_shortcut(modifier),'break')
            self.assertEqual(app.stop_key.get(),'F9')
            app._capture_shortcut(key)
            self.assertEqual(app.stop_key.get(),'Ctrl+Alt+Q')
            self.assertEqual(app.shortcut_display.get(),'Ctrl+Alt+Q')
            self.assertFalse(app._shortcut_capturing)
            # Refocusing does not rearm. Click again even while already focused.
            next_key=SimpleNamespace(keysym='F7',state=0,keycode=0x76)
            app._capture_shortcut(next_key)
            self.assertEqual(app.stop_key.get(),'Ctrl+Alt+Q')
            app._begin_shortcut_capture()
            app._capture_shortcut(next_key)
            self.assertEqual(app.stop_key.get(),'F7')
            app._set_controls(True)
            app._begin_shortcut_capture()
            app._capture_shortcut(key)
            self.assertEqual(app.stop_key.get(),'F7')
            app._set_controls(False)
            self.assertTrue(app.shortcut_entry.instate(['readonly']))
            app._begin_shortcut_capture()
            app._end_shortcut_capture()
            self.assertEqual(app.shortcut_display.get(),'F7')
            # Cancelling by clicking elsewhere keeps the last complete binding.
            app._begin_shortcut_capture()
            app._cancel_shortcut_on_click(SimpleNamespace(widget=app.target_entry))
            self.assertFalse(app._shortcut_capturing)
            self.assertEqual(app.shortcut_display.get(),'F7')
            app._capture_shortcut(key)
            self.assertEqual(app.stop_key.get(),'F7')
        finally:
            app._closing=True
            for callback in root.tk.splitlist(root.tk.call('after','info')):
                root.after_cancel(callback)
            root.destroy()

    def test_custom_start_binding_conflict_and_global_poll_guards(self):
        root=tk.Tk(); app=FishingApp(root)
        down=set()
        try:
            self.assertEqual(app.start_key.get(),'F8')
            app._begin_shortcut_capture(target='start')
            with patch('gui.messagebox.showerror') as error:
                app._capture_shortcut(SimpleNamespace(keysym='F9',state=0,keycode=0x78))
                error.assert_called_once()
            self.assertEqual(app.start_key.get(),'F8')
            app._begin_shortcut_capture(target='start')
            app._capture_shortcut(SimpleNamespace(keysym='q',state=0x20004,keycode=0x51))
            self.assertEqual(app.start_key.get(),'Ctrl+Alt+Q')
            self.assertEqual(app.start_shortcut_display.get(),'Ctrl+Alt+Q')
            with patch.object(app,'_launch') as launch:
                app._hotkey_start(); launch.assert_called_once()
                for guard in ('capture','modal','closing'):
                    app._shortcut_capturing=guard=='capture'
                    app._closing=guard=='closing'
                    with patch.object(root,'grab_current',return_value=object() if guard=='modal' else None):
                        app._poll_start_hotkey()
                        app._hotkey_start()
                    launch.assert_called_once()
                app._closing=False; app._shortcut_capturing=False
                app._poll_start_hotkey(); app._hotkey_start()
                self.assertEqual(launch.call_count,2)
            app._set_controls(True)
            self.assertTrue(app.start_shortcut_entry.instate(['disabled']))
            app._set_controls(False)
            self.assertTrue(app.start_shortcut_entry.instate(['readonly']))
        finally:
            app._closing=True
            for callback in root.tk.splitlist(root.tk.call('after','info')):
                root.after_cancel(callback)
            root.destroy()

    def test_only_log_has_scrollbar(self):
        root=tk.Tk()
        app=FishingApp(root)
        try:
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            bars=[w for w in descendants(root) if isinstance(w,ttk.Scrollbar)]
            self.assertEqual(len(bars),1)
            self.assertEqual(bars[0].master,app.log.master)
            self.assertFalse(hasattr(app,'viewport'))
            self.assertNotIn('計數',app.instructions.cget('text'))
        finally:
            app._closing=True
            for callback in root.tk.splitlist(root.tk.call('after','info')):
                root.after_cancel(callback)
            root.destroy()

    def test_every_start_resets_count_even_after_target_and_help_explains_location(self):
        root=tk.Tk()
        app=FishingApp(root)
        try:
            app.counter.update(3)
            app.target.set('5')
            app.stop_key.set('Ctrl+Alt+Q')
            with patch('gui.threading.Thread') as thread:
                thread.return_value.is_alive.return_value=False
                app.start()
                self.assertEqual(app.counter.total,0)
                self.assertIn('0',app.count_label.cget('text'))
                self.assertEqual(app.session_args.target_catches,5)
                self.assertEqual(app.session_args.stop_hotkey,'Ctrl+Alt+Q')
                self.assertIsNone(app.session_args.debug_dir)
                app.messages.put(('progress',{'catches':5}))
                app.messages.put(('done',None))
                app._poll()
                self.assertEqual(app.counter.total,5)
                with patch('gui.messagebox.showinfo') as info:
                    app.start()
                    info.assert_not_called()
                self.assertEqual(thread.call_count,2)
                self.assertEqual(app.counter.total,0)
                self.assertIn('0',app.count_label.cget('text'))
                self.assertEqual(app.session_args.target_catches,5)
                # A manual stop before the target also starts a fresh count.
                app.messages.put(('progress',{'catches':2}))
                app.messages.put(('done',None))
                app._poll()
                self.assertEqual(app.counter.total,2)
                app.start()
                self.assertEqual(app.counter.total,0)
                self.assertEqual(app.session_args.target_catches,5)
                # Double-start while actually running must not erase progress.
                app.counter.update(1)
                thread.return_value.is_alive.return_value=True
                app.start()
                self.assertEqual(app.counter.total,1)
                self.assertEqual(thread.call_count,3)
                thread.return_value.is_alive.return_value=False
                app.target.set('0')
                app.start()
                self.assertEqual(app.counter.total,0)
                self.assertEqual(app.session_args.target_catches,0)
            dialog=app.show_developer_help()
            root.update()
            body=dialog.nametowidget('content.body')
            link=dialog.nametowidget('content.project_link')
            path_link=dialog.nametowidget('content.diagnostic_link')
            self.assertIn('診斷資料位於：',body.cget('text'))
            self.assertEqual(path_link.cget('text'),str(app.diagnostic_base()))
            self.assertEqual(str(path_link.cget('cursor')),'hand2')
            with patch('gui.Path.mkdir') as mkdir,patch('gui.os.startfile') as explorer:
                path_link.event_generate('<Button-1>',x=5,y=5)
                mkdir.assert_called_once_with(parents=True,exist_ok=True)
                explorer.assert_called_once_with(str(app.diagnostic_base().resolve()))
            self.assertNotIn('固定',body.cget('text'))
            self.assertEqual(dialog.nametowidget('content.project_label').cget('text'),'項目地址：')
            self.assertEqual(link.cget('text'),PROJECT_URL)
            self.assertEqual(str(link.cget('cursor')),'hand2')
            with patch('gui.webbrowser.open_new_tab') as browser:
                link.event_generate('<Button-1>',x=5,y=5)
                browser.assert_called_once_with(PROJECT_URL)
            self.assertIs(app.show_developer_help(),dialog)
            dialog.destroy()
            for language in GAME_LANGUAGES:
                app.game_language.set(language)
                app._apply_language()
                dialog=app.show_developer_help()
                root.update()
                path_link=dialog.nametowidget('content.diagnostic_link')
                self.assertTrue(path_link.bind('<Return>'))
                self.assertTrue(path_link.bind('<space>'))
                self.assertEqual(path_link.cget('text'),str(app.diagnostic_base()))
                dialog.destroy()
        finally:
            app._closing=True
            for callback in root.tk.splitlist(root.tk.call('after','info')):
                root.after_cancel(callback)
            root.destroy()
