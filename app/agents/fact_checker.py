"""FactChecker agent for verifying suspicious claims."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from app.llm.client import get_chat_model
from app.llm.schemas import FactCheckVerdict
from app.llm.retry import safe_call_for_json, LLMCallError
from app.policies.fallbacks import fallback_factcheck
from app.logging.errors import log_error

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "fact_checker.md")


def _serialize_candidate_profile(candidate_profile: Any) -> Dict[str, Any]:
    if hasattr(candidate_profile, "model_dump"):
        return candidate_profile.model_dump()
    if isinstance(candidate_profile, dict):
        return candidate_profile
    return {"value": str(candidate_profile)}


def run_factchecker(state: Dict[str, Any], claim: str) -> FactCheckVerdict:
    llm = get_chat_model("factchecker")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    payload = {
        "candidate_profile": _serialize_candidate_profile(state.get("candidate_profile")),
        "claim": claim,
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        return safe_call_for_json(
            llm,
            messages,
            FactCheckVerdict,
            max_attempts=2,
            timeout_s=60,
            role="factchecker",
        )
    except LLMCallError as exc:
        session_id = state.get("session_id", "unknown")
        log_error(session_id, "factchecker", exc)
        return FactCheckVerdict.model_validate(fallback_factcheck(claim))
