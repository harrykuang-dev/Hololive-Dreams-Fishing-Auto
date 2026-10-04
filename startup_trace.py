"""Bounded, opt-in startup journal inside the diagnostic session only."""
from datetime import datetime
import os
from pathlib import Path
import threading

_lock = threading.Lock()
_LIMIT = 128 * 1024


def startup_log(message, directory=None):
    if not directory:
        return
    try:
        with _lock:
            base = Path(directory)
            # Shutdown already archived the session: do not recreate loose files.
            if base.exists() and any(base.glob('diagnostics-*.zip')):
                return
            base.mkdir(parents=True, exist_ok=True)
            path = base/'startup.log'
            payload = f'{datetime.now().isoformat(timespec="milliseconds")} {threading.current_thread().name} {message}\n'.encode('utf-8')
            size = path.stat().st_size if path.exists() else 0
            if size + len(payload) <= _LIMIT:
                with path.open('ab') as stream:
                    stream.write(payload)
    except OSError:
        pass  # Diagnostics must never prevent starting or stopping.


def remove_legacy_startup_logs():
    """Remove only the two journals written by the earlier development build."""
    base = Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData'/'Local'))/'HololiveFishingAuto'
    for name in ('startup.log', 'startup.log.1'):
        try:
            path = base/name
            if path.is_file() and not path.is_symlink():
                path.unlink()
        except OSError:
            pass
