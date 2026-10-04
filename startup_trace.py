"""Small startup journal, including initialization before screenshots exist."""
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import threading

_lock = threading.Lock()
_logger = None


def startup_log(message):
    global _logger
    try:
        with _lock:
            if _logger is None:
                base = Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData'/'Local'))/'HololiveFishingAuto'
                base.mkdir(parents=True, exist_ok=True)
                _logger = logging.getLogger('fishing-startup')
                _logger.setLevel(logging.INFO)
                _logger.propagate = False
                handler = RotatingFileHandler(base/'startup.log', maxBytes=128*1024, backupCount=1, encoding='utf-8')
                handler.setFormatter(logging.Formatter('%(asctime)s %(threadName)s %(message)s'))
                _logger.addHandler(handler)
            _logger.info(message)
    except Exception:
        pass  # A diagnostic write must never prevent starting/stopping.
