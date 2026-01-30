"""HiringManager agent that produces final feedback JSON."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from app.llm.client import get_chat_model
from app.llm.schemas import FinalFeedback
from app.llm.retry import safe_call_for_json, LLMCallError
from app.policies.fallbacks import fallback_final_feedback
from app.logging.errors import log_error

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "hiring_manager.md")


def run_hiring_manager(feedback_input: Dict[str, Any]) -> FinalFeedback:
    llm = get_chat_model("hiring_manager")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(feedback_input, ensure_ascii=False)},
    ]

    try:
        return safe_call_for_json(
            llm,
            messages,
            FinalFeedback,
            max_attempts=2,
            timeout_s=60,
            role="hiring_manager",
        )
    except LLMCallError as exc:
        session_id = feedback_input.get("session_id", "unknown") if isinstance(feedback_input, dict) else "unknown"
        log_error(session_id, "hiring_manager", exc)
        return FinalFeedback.model_validate(fallback_final_feedback(feedback_input))
