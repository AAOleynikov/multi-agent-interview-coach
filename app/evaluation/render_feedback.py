"""Render final feedback JSON into a readable text block."""
from __future__ import annotations

from typing import Dict, Any


def render_final_feedback(feedback: Dict[str, Any]) -> str:
    decision = feedback.get("Decision", {})
    hard = feedback.get("HardSkills", {})
    soft = feedback.get("SoftSkills", {})
    roadmap = feedback.get("Roadmap", {})

    lines = []
    lines.append("Decision")
    lines.append(f"- Grade: {decision.get('Grade')}")
    lines.append(f"- Recommendation: {decision.get('HiringRecommendation')}")
    lines.append(f"- Confidence: {decision.get('ConfidenceScore')}")

    lines.append("\nHard Skills")
    lines.append(f"- Confirmed: {', '.join(hard.get('ConfirmedSkills', []))}")
    gaps = hard.get("KnowledgeGaps", [])
    if gaps:
        lines.append("- Knowledge Gaps:")
        for gap in gaps:
            lines.append(f"  * {gap.get('topic')}: {gap.get('what_went_wrong')}")
            lines.append(f"    Correct: {gap.get('correct_answer')}")
            lines.append(f"    Evidence: {gap.get('evidence')}")

    lines.append("\nSoft Skills")
    lines.append(f"- Clarity: {soft.get('Clarity')}")
    lines.append(f"- Honesty: {soft.get('Honesty')}")
    lines.append(f"- Engagement: {soft.get('Engagement')}")
    lines.append(f"- Notes: {soft.get('Notes')}")

    lines.append("\nRoadmap")
    for step in roadmap.get("NextSteps", []):
        lines.append(f"- {step.get('topic')}: {step.get('why')}")
        resources = step.get("resources", [])
        if resources:
            lines.append(f"  Resources: {', '.join(resources)}")

    lines.append("\nSummary")
    lines.append(feedback.get("Summary", ""))

    return "\n".join(lines)

