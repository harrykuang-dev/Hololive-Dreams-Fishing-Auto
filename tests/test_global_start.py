"""Native messages go to our own thread; no keyboard/game input is sent."""
import ctypes
from ctypes import wintypes
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch
from global_hotkey import GlobalHotkey, WM_HOTKEY, windows_hotkey
from gui import FishingApp


def post_hotkey(listener,value):
    modifiers,key=windows_hotkey(value)
    post=ctypes.windll.user32.PostThreadMessageW
    post.argtypes=(wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM)
    post.restype=wintypes.BOOL
    assert post(listener.thread_id,WM_HOTKEY,listener.registration_id,modifiers|(key<<16))


class GlobalStartTests(unittest.TestCase):
    def test_windows_hotkey_modifiers_are_distinct_from_tk_lock_bits(self):
        self.assertEqual(windows_hotkey('F9'),(0,0x78))
        self.assertEqual(windows_hotkey('Ctrl+Alt+Shift+Q'),(7,ord('Q')))
        self.assertEqual(windows_hotkey('Alt+Ctrl+Q'),windows_hotkey('Ctrl+Alt+Q'))

    def test_native_message_starts_worker_without_processing_tk_events(self):
        # This unusual shortcut avoids taking a key the user normally uses.
        key='Ctrl+Alt+Shift+F23'
        root=tk.Tk(); root.withdraw()
        seen=threading.Event(); release=threading.Event(); ready=threading.Event()
        registrations=[]; calls=[]; listener=None
        try:
            with (patch('gui.GlobalHotkey'),patch('gui.startup_log'),patch('gui.run') as run):
                app=FishingApp(root)
                app.start_key.set(key);app.stop_key.set('F10');app.target.set('7')
                def fake_run(args,**callbacks):
                    calls.append((args,threading.get_ident()))
                    seen.set();release.wait(2)
                run.side_effect=fake_run
                def report(value,registered,error):
                    registrations.append((value,registered,error));ready.set()
                listener=GlobalHotkey(app._hotkey_start,report)
                listener.configure(value=key);listener.start()
                self.assertTrue(ready.wait(1));self.assertTrue(registrations[-1][1],registrations)
                post_hotkey(listener,key)
                # Deliberately never call root.update()/mainloop here.
                self.assertTrue(seen.wait(1),'Start depended on the Tk event loop')
                self.assertEqual(calls[0][0].stop_hotkey,'F10')
                self.assertEqual(calls[0][0].target_catches,7)
                self.assertEqual(calls[0][0].start_source,'hotkey')
                self.assertNotEqual(calls[0][1],threading.get_ident())
                post_hotkey(listener,key);time.sleep(.04)
                self.assertEqual(len(calls),1)  # Already running, no duplicate.
                old_id=app._run_id
                release.set();app.worker.join(1);self.assertFalse(app.worker.is_alive())
                seen.clear();post_hotkey(listener,key)
                self.assertTrue(seen.wait(1));app.worker.join(1)
                self.assertEqual(len(calls),2)
                app.messages.put((old_id,'progress',{'catches':99}))
                # Only now let the GUI consume its messages; old run ignored.
                app._poll()
                self.assertEqual(app._display_run_id,app._run_id)
                self.assertEqual(app.counter.total,0)
                self.assertFalse(app.start_button.instate(['disabled']))
        finally:
            release.set()
            if listener:
                listener.close();listener.thread.join(1)
                self.assertFalse(listener.thread.is_alive())
                self.assertIsNone(listener.registration_id)
            for callback in root.tk.splitlist(root.tk.call('after','info')):
                root.after_cancel(callback)
            root.destroy()

    def test_registration_conflict_is_reported_and_rebinding_recovers(self):
        key='Ctrl+Alt+Shift+F22';ready=threading.Event();reports=[]
        first=GlobalHotkey(lambda:None,lambda *args:ready.set())
        second_ready=threading.Event()
        def report(*args):reports.append(args);second_ready.set()
        second=GlobalHotkey(lambda:None,report)
        try:
            first.configure(value=key);first.start();self.assertTrue(ready.wait(1))
            self.assertIsNotNone(first.registration_id)
            second.configure(value=key);second.start();self.assertTrue(second_ready.wait(1))
            self.assertFalse(reports[-1][1],reports)
            second_ready.clear();second.configure(value='Ctrl+Alt+Shift+F21')
            self.assertTrue(second_ready.wait(1));self.assertTrue(reports[-1][1],reports)
        finally:
            for listener in (first,second):
                listener.close()
                if listener.thread:listener.thread.join(1)
