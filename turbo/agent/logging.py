"""Structured logging configuration for Turbo agents.

Provides JSON-formatted logging with contextual fields (agent_id,
session_id, project_id) for production observability.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON log formatter with Turbo agent context."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add contextual fields if present
        for field in ("agent_id", "session_id", "project_id", "tool_name", "cost_usd"):
            value = getattr(record, field, None)
            if value is not None:
                entry[field] = value

        if record.exc_info and record.exc_info[1]:
            entry["error"] = str(record.exc_info[1])
            entry["error_type"] = type(record.exc_info[1]).__name__

        return json.dumps(entry)


def configure_agent_logging(
    level: str = "INFO",
    json_output: bool = True,
) -> None:
    """Configure logging for Turbo agent operations.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        json_output: If True, use structured JSON format. If False, use plain text.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    agent_logger = logging.getLogger("turbo.agent")
    agent_logger.setLevel(log_level)

    # Avoid duplicate handlers on repeated calls
    if not agent_logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(log_level)

        if json_output:
            handler.setFormatter(StructuredFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            )

        agent_logger.addHandler(handler)

    # Don't propagate to root logger
    agent_logger.propagate = False
