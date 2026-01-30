"""Routing rules for robustness-aware branching."""
from __future__ import annotations

from app.policies.robustness import RobustnessDetection


def choose_route(stop_requested: bool, det: RobustnessDetection) -> str:
    if stop_requested:
        return "final"
    if det.role_reversal:
        return "answer_candidate"
    if det.hallucination_claim:
        return "hallucination"
    if det.off_topic:
        return "refocus"
    return "normal"

