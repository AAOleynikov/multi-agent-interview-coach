"""Robustness detectors for off-topic, role reversal, hallucination, and evasive answers."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Optional


@dataclass
class RobustnessDetection:
    off_topic: bool
    role_reversal: bool
    hallucination_claim: bool
    evasive: bool
    reason: str
    candidate_question: Optional[str]
    suspicious_claim: Optional[str]


def _extract_candidate_question(text: str) -> Optional[str]:
    if "?" not in text:
        return None
    parts = [p.strip() for p in re.split(r"[\n\.?!]", text) if p.strip()]
    for part in reversed(parts):
        if "?" in part:
            return part + "?"
    return text.strip()


def detect_robustness(state: Dict[str, Any]) -> RobustnessDetection:
    user_message = (state.get("user_message") or "").strip()
    observer_robustness = {}
    if isinstance(state.get("observer_json"), dict):
        observer_robustness = state.get("observer_json", {}).get("robustness", {}) or {}

    # All robustness signals come from Observer (LLM).
    off_topic = bool(observer_robustness.get("off_topic")) if isinstance(observer_robustness, dict) else False
    role_reversal = bool(observer_robustness.get("role_reversal")) if isinstance(observer_robustness, dict) else False
    candidate_question = _extract_candidate_question(user_message) if role_reversal else None

    # Hallucination signal is taken only from Observer (LLM).
    hallucination_claim = bool(observer_robustness.get("hallucination_claim")) if isinstance(observer_robustness, dict) else False
    suspicious_claim = user_message if hallucination_claim else None

    evasive = bool(observer_robustness.get("evasive")) if isinstance(observer_robustness, dict) else False

    reason_parts = []
    if off_topic:
        reason_parts.append("off_topic keywords")
    if role_reversal:
        reason_parts.append("candidate asked about process")
    if hallucination_claim:
        reason_parts.append("observer hallucination signal")
    if evasive:
        reason_parts.append("evasive phrasing/short answer")
    reason = ", ".join(reason_parts) if reason_parts else "no issues detected"

    return RobustnessDetection(
        off_topic=off_topic,
        role_reversal=role_reversal,
        hallucination_claim=hallucination_claim,
        evasive=evasive,
        reason=reason,
        candidate_question=candidate_question,
        suspicious_claim=suspicious_claim,
    )
