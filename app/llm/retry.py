"""Centralized safe LLM JSON calls with retries and repair."""
from __future__ import annotations

import time
from typing import Any, Type

from app.llm.json_parser import call_llm_for_json, JsonSchemaValidationError


class LLMCallError(Exception):
    def __init__(self, role: str, message: str, last_response: str | None = None, cause: Exception | None = None):
        super().__init__(message)
        self.role = role
        self.last_response = last_response
        self.cause = cause


def _clip(text: str | None, limit: int = 800) -> str | None:
    if text is None:
        return None
    return text if len(text) <= limit else text[:limit] + "..."


def safe_call_for_json(llm, messages, schema: Type[Any], max_attempts: int, timeout_s: float, role: str):
    last_err: Exception | None = None
    last_response: str | None = None

    for attempt in range(max_attempts):
        try:
            # Prefer native timeout on model if available
            if hasattr(llm, "timeout"):
                setattr(llm, "timeout", timeout_s)
            result = call_llm_for_json(llm, messages, schema, max_attempts=1)
            return result
        except JsonSchemaValidationError as exc:
            last_err = exc
            last_response = _clip(exc.original_text)
        except Exception as exc:  # network/timeout errors
            last_err = exc
        if attempt < max_attempts - 1:
            time.sleep(0.5 * (attempt + 1))

    raise LLMCallError(
        role=role,
        message=f"LLM call failed for role={role}: {last_err}",
        last_response=_clip(last_response),
        cause=last_err,
    )
