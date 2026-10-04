import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from diagnostics import DiagnosticWriter
from startup_trace import startup_log, remove_legacy_startup_logs, _LIMIT


class StartupTraceTests(unittest.TestCase):
    def test_normal_mode_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, LOCALAPPDATA=folder):
            startup_log('connecting')
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_developer_log_is_bounded_archived_and_not_recreated(self):
        with tempfile.TemporaryDirectory() as folder:
            startup_log('finding game', folder)
            for _ in range(200):
                startup_log('x'*1024, folder)
            self.assertLessEqual(Path(folder,'startup.log').stat().st_size, _LIMIT)
            archive = DiagnosticWriter(folder).close()
            with zipfile.ZipFile(archive) as z:
                self.assertIn(b'finding game', z.read('startup.log'))
                self.assertIsNone(z.testzip())
            startup_log('finished', folder)
            self.assertEqual(list(Path(folder).iterdir()), [archive])

    def test_legacy_cleanup_keeps_other_files(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, LOCALAPPDATA=folder):
            base=Path(folder,'HololiveFishingAuto')
            base.mkdir()
            for name in ('startup.log','startup.log.1','keep.txt'):
                (base/name).write_text('keep')
            remove_legacy_startup_logs()
            self.assertEqual([p.name for p in base.iterdir()], ['keep.txt'])

    def test_gui_archives_failure_before_capture_initialization(self):
        import queue
        import threading
        from gui import FishingApp
        with tempfile.TemporaryDirectory() as folder:
            app=FishingApp.__new__(FishingApp)
            app.stop_event=threading.Event()
            app.messages=queue.Queue()
            args=FishingApp.bot_args('zh-TW')
            args.debug_dir=folder
            with patch('gui.run',side_effect=RuntimeError('window initialization failed')):
                app._run_bot(args, 1)
            archives=list(Path(folder).glob('*.zip'))
            self.assertEqual(len(archives),1)
            self.assertEqual(list(Path(folder).iterdir()),archives)
            with zipfile.ZipFile(archives[0]) as z:
                self.assertIn(b'window initialization failed',z.read('startup.log'))

    def test_gui_does_not_repackage_failed_existing_diagnostics(self):
        import queue
        import threading
        from gui import FishingApp
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'trace.csv').write_text('existing evidence')
            app=FishingApp.__new__(FishingApp)
            app.stop_event=threading.Event()
            app.messages=queue.Queue()
            args=FishingApp.bot_args('zh-TW')
            args.debug_dir=folder
            with patch('gui.run',side_effect=RuntimeError('packing failed')), patch('diagnostics.DiagnosticWriter') as writer:
                app._run_bot(args,1)
            writer.assert_not_called()
            self.assertEqual(Path(folder,'trace.csv').read_text(),'existing evidence')
