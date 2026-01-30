"""Stop intent classifier agent."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from app.llm.client import get_chat_model
from app.llm.retry import safe_call_for_json, LLMCallError
from app.llm.schemas import StopIntentOutput
from app.logging.errors import log_error

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "stop_intent.md")


def run_stop_intent(state: Dict[str, Any]) -> StopIntentOutput:
    llm = get_chat_model("stop_intent")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_msg = state.get("user_message", "") or ""
    if not user_msg:
        # CLI уже должен блокировать пустые ответы, но оставим страховку.
        return StopIntentOutput(stop=False, confidence=0, rationale="empty message")

    payload = {
        "task": "technical interview",
        "user_message": user_msg,
        "note": "Detect if the user wants to end the interview and receive final feedback.",
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        return safe_call_for_json(
            llm,
            messages,
            StopIntentOutput,
            max_attempts=2,
            timeout_s=15,
            role="stop_intent",
        )
    except LLMCallError as exc:
        session_id = state.get("session_id", "unknown")
        log_error(session_id, "stop_intent", exc)
        return StopIntentOutput.model_validate({
            "stop": False,
            "confidence": 0,
            "rationale": "Fallback: classifier unavailable.",
        })
