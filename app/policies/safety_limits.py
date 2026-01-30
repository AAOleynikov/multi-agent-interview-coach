"""Normalization and safety limits for text inputs."""
from __future__ import annotations

import re


def normalize_text(s: str, max_len: int) -> str:
    if s is None:
        return ""
    cleaned = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\u0400-\u04FF]", " ", str(s))
    cleaned = cleaned.strip()
    if not cleaned:
        return ""
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned
