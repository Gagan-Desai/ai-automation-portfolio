
import logging
import json
from datetime import datetime, timezone

def setup_logger():
    logger = logging.getLogger("document_processor")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:  # avoid duplicate handlers if this gets imported more than once
        handler = logging.FileHandler("processing.log")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger

def log_event(logger, level: str, message: str, **context):
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
        **context
    }
    getattr(logger, level.lower())(json.dumps(payload))