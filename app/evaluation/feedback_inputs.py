"""Build compact inputs for the HiringManager agent."""
from __future__ import annotations

from typing import Any, Dict, List


def _summarize_internal_thoughts(text: str) -> str:
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return text[:200]
    return " ".join(lines[:2])[:200]


def _collect_notable_behaviors(turns: List[Dict[str, Any]]) -> List[str]:
    behaviors = set()
    for turn in turns:
        thoughts = turn.get("internal_thoughts", "") or ""
        if "route=hallucination" in thoughts:
            behaviors.add("hallucination claim")
        if "route=answer_candidate" in thoughts:
            behaviors.add("role reversal")
        if "route=refocus" in thoughts:
            behaviors.add("off topic attempt")
    return sorted(behaviors)


def _serialize_candidate_profile(candidate_profile: Any) -> Dict[str, Any]:
    if hasattr(candidate_profile, "model_dump"):
        return candidate_profile.model_dump()
    if isinstance(candidate_profile, dict):
        return candidate_profile
    return {"value": str(candidate_profile)}


def build_feedback_input(state: Dict[str, Any], log_data: Dict[str, Any]) -> Dict[str, Any]:
    turns = log_data.get("turns", []) if isinstance(log_data, dict) else []
    summary_turns = []
    for turn in turns:
        summary_turns.append(
            {
                "turn_id": turn.get("turn_id"),
                "question": turn.get("agent_visible_message"),
                "answer": turn.get("user_message"),
                "notes": _summarize_internal_thoughts(turn.get("internal_thoughts", "")),
            }
        )

    skill_matrix = state.get("skill_matrix", {}) if isinstance(state.get("skill_matrix"), dict) else {}
    confirmed = []
    gaps = []
    for topic, info in skill_matrix.items():
        status = (info or {}).get("status") if isinstance(info, dict) else None
        if status == "confirmed":
            confirmed.append(topic)
        if status == "gap":
            gaps.append(topic)

    highlights = {
        "confirmed": confirmed,
        "gaps": gaps,
        "notable_behaviors": _collect_notable_behaviors(turns),
    }

    return {
        "session_id": state.get("session_id"),
        "candidate_profile": _serialize_candidate_profile(state.get("candidate_profile")),
        "final_difficulty": state.get("difficulty"),
        "skill_matrix": skill_matrix,
        "turns": summary_turns,
        "highlights": highlights,
    }
