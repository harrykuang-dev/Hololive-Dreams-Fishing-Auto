import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

import cv2
import numpy as np

from diagnostics import BoundedTrace, DiagnosticWriter, IMAGE_LIMIT, compact_jpeg, cleanup_archived_files


class DiagnosticsTests(unittest.TestCase):
    def test_noisy_4k_image_respects_byte_and_dimension_budget(self):
        frame = np.random.default_rng(1).integers(0,256,(2160,3840,3),dtype=np.uint8)
        original = frame.copy()
        payload, shape, _ = compact_jpeg(frame)
        self.assertLessEqual(len(payload), IMAGE_LIMIT)
        decoded = cv2.imdecode(np.frombuffer(payload,np.uint8),1)
        self.assertEqual(decoded.shape[:2],shape)
        self.assertLessEqual(shape[1],1280)
        np.testing.assert_array_equal(frame,original)

    def test_slow_encoder_does_not_block_submit_and_queue_stays_bounded(self):
        entered, release = threading.Event(), threading.Event()
        def encode(frame):
            entered.set()
            self.assertTrue(release.wait(3))
            return b'jpg',(1,1),82
        with tempfile.TemporaryDirectory() as folder, patch('diagnostics.compact_jpeg',side_effect=encode):
            writer = DiagnosticWriter(folder)
            writer.submit('initial.jpg',np.zeros((1,1,3),np.uint8))
            self.assertTrue(entered.wait(2))
            try:
                for i in range(30):
                    writer.submit(f'{i}.jpg',np.zeros((1,1,3),np.uint8))
                with writer._condition:
                    self.assertEqual(len(writer._jobs),3)
                self.assertEqual(writer.dropped,27)
            finally:
                release.set()
                archive = writer.close()
            with zipfile.ZipFile(archive) as z:
                self.assertIn('29.jpg',z.namelist())
                self.assertNotIn('0.jpg',z.namelist())

    def test_retention_and_archive_exclude_large_video_and_unrelated_files(self):
        with tempfile.TemporaryDirectory() as folder, patch('diagnostics.IMAGE_COUNT',3):
            frame = np.zeros((30,40,3),np.uint8)
            writer = DiagnosticWriter(folder)
            # Wait deterministically for each job, without depending on timing.
            for i in range(5):
                writer.submit(f'{i}.jpg',frame)
                with writer._condition:
                    self.assertTrue(writer._condition.wait_for(lambda: writer.written >= i+1, timeout=2))
            writer.submit('latest.jpg',frame)
            Path(folder,'game.mp4').write_bytes(b'large video')
            Path(folder,'unrelated.txt').write_text('private')
            trace = BoundedTrace(folder,'seconds,state\n')
            trace.write('0,tap\n')
            trace.close()
            archive = writer.close()
            self.assertEqual(len(list(Path(folder).glob('*.jpg'))),0)
            self.assertEqual(set(p.name for p in Path(folder).iterdir()),{archive.name,'game.mp4','unrelated.txt'})
            self.assertRegex(archive.name,r'^diagnostics-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.zip$')
            with zipfile.ZipFile(archive) as z:
                self.assertNotIn('game.mp4',z.namelist())
                self.assertNotIn('unrelated.txt',z.namelist())
                self.assertIn('latest.jpg',z.namelist())
                self.assertIn('trace.csv',z.namelist())
                self.assertFalse(json.loads(z.read('diagnostics.json'))['live_success_claim'])

    def test_encoding_failure_is_reported_and_shutdown_finishes(self):
        with tempfile.TemporaryDirectory() as folder, patch('diagnostics.compact_jpeg',side_effect=OSError('disk test')):
            writer = DiagnosticWriter(folder)
            writer.submit('test.jpg',np.zeros((1,1,3),np.uint8))
            archive = writer.close()
            self.assertEqual(writer.error,'disk test')
            self.assertFalse(writer._thread.is_alive())
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(json.loads(z.read('diagnostics.json'))['error'],'disk test')

    def test_archive_write_failure_keeps_original_diagnostics(self):
        with tempfile.TemporaryDirectory() as folder:
            writer=DiagnosticWriter(folder)
            Path(folder,'trace.csv').write_text('important trace',encoding='utf-8')
            with patch('diagnostics.zipfile.ZipFile',side_effect=OSError('archive failed')):
                with self.assertRaisesRegex(OSError,'archive failed'):
                    writer.close()
            self.assertEqual(Path(folder,'trace.csv').read_text(),'important trace')
            self.assertTrue(Path(folder,'diagnostics.json').is_file())

    def test_changed_original_prevents_any_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder,'diagnostics.zip')
            with zipfile.ZipFile(a,'w') as z:
                z.writestr('latest.jpg',b'original')
                z.writestr('trace.csv',b'old')
            Path(folder,'latest.jpg').write_bytes(b'original')
            Path(folder,'trace.csv').write_bytes(b'changed')
            with self.assertRaisesRegex(OSError,'differs'):
                cleanup_archived_files(a)
            self.assertTrue(Path(folder,'latest.jpg').exists())
            self.assertEqual(Path(folder,'trace.csv').read_bytes(),b'changed')

    def test_close_twice_preserves_the_complete_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            writer=DiagnosticWriter(folder)
            Path(folder,'trace.csv').write_text('trace',encoding='utf-8')
            archive=writer.close()
            payload=archive.read_bytes()
            self.assertEqual(writer.close(),archive)
            self.assertEqual(archive.read_bytes(),payload)
            self.assertEqual(list(Path(folder).iterdir()),[archive])

    def test_trace_rotation_keeps_header_and_only_two_recent_segments(self):
        with tempfile.TemporaryDirectory() as folder, patch('diagnostics.TRACE_LIMIT',40):
            trace = BoundedTrace(folder,'seconds,state\n')
            for i in range(10):
                trace.write(f'{i},unknown\n')
            trace.close()
            for name in ('trace.csv','trace.previous.csv'):
                payload = Path(folder,name).read_bytes()
                self.assertLessEqual(len(payload),40)
                self.assertTrue(payload.startswith(b'seconds,state\n'))
            self.assertIn('9,unknown',Path(folder,'trace.csv').read_text())

    def test_gui_runtime_releases_input_before_archiving_real_diagnostics(self):
        from gui import FishingApp
        from bot_vision import Detection
        import auto_fishing
        original_close = DiagnosticWriter.close
        with tempfile.TemporaryDirectory() as folder:
            args = FishingApp.bot_args('en')
            args.debug_dir = folder
            args.target_catches = 1
            args.fps = 1000
            sequence = [Detection(track_present=True,scene='reel'),
                        Detection(catch_result=True,scene='result_continue')]
            with (patch('auto_fishing.WindowCapture') as capture,
                  patch('auto_fishing.MouseController') as mouse,
                  patch('auto_fishing.win32gui.GetForegroundWindow',return_value=123),
                  patch('auto_fishing.win32api.GetAsyncKeyState',return_value=0),
                  patch('auto_fishing.ReelTracker.update',return_value=None),
                  patch('auto_fishing.analyze',side_effect=sequence),
                  patch('auto_fishing.signal.signal'),
                  patch.object(auto_fishing.sys,'stdout',None)):
                capture.return_value.hwnd = 123
                capture.return_value.grab.return_value = np.zeros((180,320,3),np.uint8)
                mouse.return_value.input_down_count = 0
                mouse.return_value.input_move_count = 0
                def close_after_input(writer, *values, **kwargs):
                    mouse.return_value.close.assert_called_once()
                    capture.return_value.close.assert_called_once()
                    return original_close(writer,*values,**kwargs)
                with patch('auto_fishing.DiagnosticWriter.close',autospec=True,side_effect=close_after_input):
                    self.assertEqual(auto_fishing.run(args),0)
            with zipfile.ZipFile(next(Path(folder).glob('diagnostics-*.zip'))) as z:
                self.assertIn('catch_000001.jpg',z.namelist())
                self.assertIn('input_down_count',z.read('trace.csv').decode('utf-8'))
                self.assertFalse(any(name.endswith('.png') for name in z.namelist()))


if __name__ == '__main__':
    unittest.main()
