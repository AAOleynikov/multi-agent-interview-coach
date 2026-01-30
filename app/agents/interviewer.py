"""Interviewer agent that generates candidate-facing messages."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from app.llm.client import get_chat_model
from app.llm.schemas import InterviewerOutput
from app.llm.retry import safe_call_for_json, LLMCallError
from app.policies.fallbacks import fallback_interviewer
from app.memory.controls import history_tail
from app.logging.errors import log_error

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "interviewer.md")


def _serialize_candidate_profile(candidate_profile: Any) -> Dict[str, Any]:
    if hasattr(candidate_profile, "model_dump"):
        return candidate_profile.model_dump()
    if isinstance(candidate_profile, dict):
        return candidate_profile
    return {"value": str(candidate_profile)}


def run_interviewer(state: Dict[str, Any]) -> InterviewerOutput:
    """
    Uses observer_json.next_action + context to generate candidate-facing message.
    """
    llm = get_chat_model("interviewer")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    history = state.get("history", []) or []
    observer_next_action = {}
    observer_instruction = None
    if isinstance(state.get("observer_json"), dict):
        observer_next_action = state.get("observer_json", {}).get("next_action", {})
        if isinstance(observer_next_action, dict):
            observer_instruction = observer_next_action.get("instruction_to_interviewer")

    payload = {
        "candidate_profile": _serialize_candidate_profile(state.get("candidate_profile")),
        "history_tail": history_tail(history, max_items=12),
        "asked_questions": state.get("asked_questions", []),
        "difficulty": state.get("difficulty", 1),
        "observer_next_action": observer_next_action,
        "action_type": state.get("action_type"),
        "planned_question": state.get("planned_question"),
        "planned_response": state.get("planned_response"),
        "observer_instruction": observer_instruction,
        "factcheck_json": state.get("factcheck_json"),
        "factcheck_note": None,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        return safe_call_for_json(
            llm,
            messages,
            InterviewerOutput,
            max_attempts=2,
            timeout_s=60,
            role="interviewer",
        )
    except LLMCallError as exc:
        session_id = state.get("session_id", "unknown")
        log_error(session_id, "interviewer", exc)
        return InterviewerOutput.model_validate(fallback_interviewer(state))
