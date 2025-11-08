"""
Structured logging configuration for Pombi AI Assistant
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime


class StructuredLogger(logging.Logger):
    """Custom logger with structured JSON output"""

    def _log(
        self,
        level: int,
        msg: str,
        args: Any,
        exc_info: Any = None,
        extra: Any = None,
        stack_info: bool = False,
    ) -> None:
        """Override to add structured logging"""
        if extra is None:
            extra = {}

        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": logging.getLevelName(level),
            "message": msg,
            "logger": self.name,
            **extra,
        }

        # Add exception info if present
        if exc_info:
            log_entry["exception"] = self.formatException(exc_info)

        # Format as JSON
        json_msg = json.dumps(log_entry, default=str)

        # Call parent with JSON-formatted message
        super()._log(level, json_msg, (), exc_info, extra, stack_info)


def setup_logging(name: str) -> StructuredLogger:
    """Set up structured logging for a module"""
    logging.setLoggerClass(StructuredLogger)

    logger = logging.getLogger(name)

    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger.addHandler(handler)
        logger.propagate = False

    return logger