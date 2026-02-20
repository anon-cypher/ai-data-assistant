import logging
import os
import traceback
from logging.handlers import TimedRotatingFileHandler

from app.utils.config import LOG_DIR, LOG_FILE, LOG_LEVEL, LOG_ROTATION_WHEN, LOG_ROTATION_INTERVAL, LOG_BACKUP_COUNT


def _ensure_log_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_logger(name: str = "ai_data_assistant") -> logging.Logger:
    """Return a configured logger instance.

    - Creates a `logs/` directory if missing.
    - Adds a `TimedRotatingFileHandler` and a console handler.
    - Rotation schedule is configurable via `app.utils.config`.

    Usage:
      from app.utils.logging import get_logger
      logger = get_logger(__name__)
      logger.info("started")

    Args:
      name: logger name.

    Returns:
      Configured `logging.Logger`.
    """
    logger = logging.getLogger(name)
    if getattr(logger, "_configured", False):
        return logger

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    # Formatter
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    formatter = logging.Formatter(fmt)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler with timed rotation
    _ensure_log_dir(LOG_DIR)
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    try:
        fh = TimedRotatingFileHandler(log_path, when=LOG_ROTATION_WHEN, interval=LOG_ROTATION_INTERVAL, backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception:
        # If file handler cannot be created, log the exception to console and continue
        logger.exception("Failed to create TimedRotatingFileHandler")

    # mark configured to avoid duplicate handlers on repeated imports
    logger._configured = True
    return logger


def log_exception(logger: logging.Logger, exc: Exception, msg: str | None = None) -> None:
    """Log an exception with full traceback using the provided logger.

    Args:
      logger: Logger returned by `get_logger()`.
      exc: Exception object (can be caught exception).
      msg: Optional message prefix.
    """
    if msg:
        logger.error("%s: %s", msg, str(exc))
    # include full traceback
    tb = traceback.format_exc()
    logger.error("Traceback:\n%s", tb)
