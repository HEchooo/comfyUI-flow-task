from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def _daily_log_namer(default_name: str) -> str:
    directory = os.path.dirname(default_name)
    suffix = os.path.basename(default_name).rsplit(".", 1)[-1]
    try:
        parsed = datetime.strptime(suffix, "%Y-%m-%d")
    except ValueError:
        return default_name
    return os.path.join(directory, parsed.strftime("%Y_%m_%d.log"))


def setup_logging(level: str, log_dir: str) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_flow_task_logging_configured", False):
        return

    log_level = getattr(logging, level.upper(), logging.INFO)
    resolved_log_dir = Path(log_dir)
    if not resolved_log_dir.is_absolute():
        resolved_log_dir = Path(__file__).resolve().parents[2] / resolved_log_dir
    resolved_log_dir.mkdir(parents=True, exist_ok=True)

    app_log_path = resolved_log_dir / "app.log"

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    file_handler = TimedRotatingFileHandler(
        filename=str(app_log_path),
        when="midnight",
        interval=1,
        backupCount=0,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.namer = _daily_log_namer
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger._flow_task_logging_configured = True

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(log_level)
