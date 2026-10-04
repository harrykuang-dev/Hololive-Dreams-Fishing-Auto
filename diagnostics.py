"""Bounded local diagnostics; image encoding never runs on the control thread."""
from collections import deque
from pathlib import Path
import json
import threading
import time
import zipfile

import cv2


IMAGE_LIMIT = 192 * 1024
IMAGE_COUNT = 64
TRACE_LIMIT = 4 * 1024 * 1024


def compact_jpeg(frame):
    """Keep diagnostic UI readable at up to 1280px, with a hard byte limit."""
    h, w = frame.shape[:2]
    scale = min(1., 1280/w)
    small = cv2.resize(frame, (round(w*scale), round(h*scale)), interpolation=cv2.INTER_AREA) if scale < 1 else frame
    for quality in (82, 72, 62, 50, 38):
        ok, encoded = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not ok:
            raise OSError('JPEG encoding failed')
        if encoded.nbytes <= IMAGE_LIMIT:
            return encoded.tobytes(), small.shape[:2], quality
    # High-entropy screenshots may still exceed the budget. Only diagnostic
    # copies shrink; analyze() continues to use the original captured frame.
    while encoded.nbytes > IMAGE_LIMIT:
        h, w = small.shape[:2]
        small = cv2.resize(small, (max(1, round(w*.8)), max(1, round(h*.8))), interpolation=cv2.INTER_AREA)
        ok, encoded = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 50])
        if not ok:
            raise OSError('JPEG encoding failed')
    return encoded.tobytes(), small.shape[:2], 50


class DiagnosticWriter:
    """At most three pending frames; coalesce latest and discard old evidence.

    Callers transfer ownership of a captured frame (never mutate it later).
    Annotation, resizing, encoding and disk writes all happen in this worker.
    close() is called after releasing mouse input and closing the trace.
    """
    def __init__(self, directory, annotate=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.annotate = annotate
        self._condition = threading.Condition()
        self._jobs = deque()
        self._closing = False
        self._retained = deque()
        self.dropped = 0
        self.written = 0
        self.write_ms = 0.
        self.max_write_ms = 0.
        self.error = None
        self.runtime_error = None
        self._thread = threading.Thread(target=self._work, name='diagnostic-writer', daemon=True)
        self._thread.start()

    def submit(self, name, frame, detection=None):
        if Path(name).name != name or not name.endswith('.jpg'):
            raise ValueError('Diagnostic image must be a local JPEG filename')
        with self._condition:
            if self._closing or self.error:
                return False
            for old in list(self._jobs):
                if old[0] == name:
                    self._jobs.remove(old)
                    self.dropped += 1
            if len(self._jobs) >= 3:
                self._jobs.popleft()
                self.dropped += 1
            self._jobs.append((name, frame, detection))
            self._condition.notify()
        return True

    def _work(self):
        try:
            while True:
                with self._condition:
                    self._condition.wait_for(lambda: self._jobs or self._closing)
                    if not self._jobs:
                        return
                    name, frame, detection = self._jobs.popleft()
                started = time.perf_counter()
                if detection is not None and self.annotate:
                    frame = self.annotate(frame, detection, detection.scene)
                payload, _, _ = compact_jpeg(frame)
                target = self.directory / name
                target.write_bytes(payload)
                if name != 'latest.jpg':
                    self._retained.append(target)
                    while len(self._retained) > IMAGE_COUNT:
                        self._retained.popleft().unlink(missing_ok=True)
                elapsed = (time.perf_counter()-started)*1000
                self.write_ms = elapsed
                self.max_write_ms = max(self.max_write_ms, elapsed)
                with self._condition:
                    self.written += 1
                    self._condition.notify_all()
        except Exception as exc:
            self.error = str(exc)
            with self._condition:
                self.dropped += len(self._jobs)
                self._jobs.clear()

    def close(self, timeout=5.):
        with self._condition:
            self._closing = True
            self._condition.notify()
        self._thread.join(timeout)
        if self._thread.is_alive():
            self.error = 'Diagnostic worker did not finish within 5 seconds; ZIP was not created'
            return None
        manifest = {
            'format': 1, 'version': '1.1-dev', 'image_max_bytes': IMAGE_LIMIT,
            'image_max_width': 1280, 'retained_image_limit': IMAGE_COUNT,
            'images_written': self.written, 'queued_frames_dropped': self.dropped,
            'max_image_write_ms': round(self.max_write_ms, 2), 'error': self.error,
            'runtime_error': self.runtime_error,
            'coordinates': 'trace and annotations refer to original client pixels before JPEG resize',
            'retention': 'last 64 event images plus latest; last two 4 MiB trace segments',
            'video': 'game.mp4 is optional and excluded from diagnostics.zip',
            'live_success_claim': False,
        }
        (self.directory/'diagnostics.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        # An explicit file list excludes arbitrary files and optional large video.
        paths = [*self._retained, self.directory/'latest.jpg',
                 self.directory/'trace.previous.csv', self.directory/'trace.csv',
                 self.directory/'diagnostics.json']
        temporary = self.directory/'diagnostics.zip.tmp'
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in paths:
                if path.is_file():
                    archive.write(path, path.name)
        output = self.directory/'diagnostics.zip'
        temporary.replace(output)
        return output


class BoundedTrace:
    """Keep the most recent two segments, each with its own CSV header."""
    def __init__(self, directory, header):
        self.path = Path(directory)/'trace.csv'
        self.header = header
        self._file = self.path.open('w', encoding='utf-8', newline='')
        self._file.write(header)
        self._bytes = len(header.encode('utf-8'))

    def write(self, line):
        size = len(line.encode('utf-8'))
        if self._bytes+size > TRACE_LIMIT:
            self._file.close()
            self.path.replace(self.path.with_name('trace.previous.csv'))
            self._file = self.path.open('w', encoding='utf-8', newline='')
            self._file.write(self.header)
            self._bytes = len(self.header.encode('utf-8'))
        self._file.write(line)
        self._bytes += size

    def flush(self):
        self._file.flush()

    def close(self):
        self._file.close()
