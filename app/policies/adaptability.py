"""Deterministic adaptability rules for difficulty and next action type."""
from __future__ import annotations

from typing import Dict, Optional


def apply_difficulty(difficulty: int, delta: int) -> int:
    base = int(difficulty or 1)
    delta_val = int(delta or 0)
    new_val = base + delta_val
    return max(1, min(5, new_val))


def decide_action_type(observer_json: Dict[str, object], prev_action_type: Optional[str] = None) -> str:
    robustness = observer_json.get("robustness", {}) if isinstance(observer_json, dict) else {}
    if isinstance(robustness, dict):
        if robustness.get("off_topic"):
            return "refocus"
        if robustness.get("role_reversal"):
            return "answer_candidate"

    answer_quality = observer_json.get("answer_quality", {}) if isinstance(observer_json, dict) else {}
    correctness = None
    confidence = None
    if isinstance(answer_quality, dict):
        correctness = answer_quality.get("correctness")
        confidence = answer_quality.get("confidence")

    if correctness in ("wrong", "low", "incorrect") or confidence in ("low", 0, 1):
        return "simplify"
    if correctness in ("partial", "mixed"):
        return "clarify"

    if prev_action_type == "simplify":
        return "hint"

    return "ask"

