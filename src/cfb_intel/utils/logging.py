"""Structured logging setup."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from cfb_intel.config import LOG_DIR


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key.startswith("cfb_"):
                payload[key[4:]] = value
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    file_handler = logging.FileHandler(LOG_DIR / "update.log", encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())

    root.addHandler(stream)
    root.addHandler(file_handler)

