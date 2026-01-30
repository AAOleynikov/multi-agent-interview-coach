"""Utilities for interview log file paths."""
from __future__ import annotations

import os


def make_log_path(session_id: str) -> str:
    """Return the canonical log path for a given session id."""
    return os.path.join("logs", session_id, "interview_log.json")

