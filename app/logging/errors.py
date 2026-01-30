"""Error logging helpers."""
from __future__ import annotations

import os
import time
import traceback


def log_error(session_id: str, where: str, exc: Exception) -> None:
    log_dir = os.path.join("logs", session_id)
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "errors.log")
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    entry = f"[{ts}] {where} {type(exc).__name__}: {exc}\n{tb}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)
