"""Observer agent that evaluates candidate responses with strict JSON output."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from app.llm.client import get_chat_model
from app.llm.schemas import ObserverOutput
from app.llm.retry import safe_call_for_json, LLMCallError
from app.policies.fallbacks import fallback_observer
from app.logging.errors import log_error

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "observer.md")


def _serialize_candidate_profile(candidate_profile: Any) -> Dict[str, Any]:
    if hasattr(candidate_profile, "model_dump"):
        return candidate_profile.model_dump()
    if isinstance(candidate_profile, dict):
        return candidate_profile
    return {"value": str(candidate_profile)}


def _get_last_interviewer_message(history: list[Dict[str, Any]]) -> str:
    for item in reversed(history):
        if item.get("role") == "interviewer":
            return item.get("content", "")
    return ""


def run_observer(state: Dict[str, Any]) -> ObserverOutput:
    """
    Вход: state (candidate_profile, history, last interviewer question, user_message,
    asked_questions, skill_matrix, difficulty)
    Выход: ObserverOutput
    """
    llm = get_chat_model("observer")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    history = state.get("history", []) or []
    context_payload = {
        "candidate_profile": _serialize_candidate_profile(state.get("candidate_profile")),
        "difficulty": state.get("difficulty", 1),
        "asked_questions": state.get("asked_questions", []),
        "skill_matrix": state.get("skill_matrix", {}),
        "last_interviewer_message": _get_last_interviewer_message(history),
        "user_message": state.get("user_message", ""),
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(context_payload, ensure_ascii=False)},
    ]

    try:
        return safe_call_for_json(
            llm,
            messages,
            ObserverOutput,
            max_attempts=2,
            timeout_s=60,
            role="observer",
        )
    except LLMCallError as exc:
        session_id = state.get("session_id", "unknown")
        log_error(session_id, "observer", exc)
        return ObserverOutput.model_validate(fallback_observer(state))
