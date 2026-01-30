"""Fallback logic when LLM calls fail."""
from __future__ import annotations

from typing import Any, Dict

from app.policies.question_bank import get_candidates
from app.policies.topic_manager import select_next_topic
from app.llm.schemas import FinalFeedback


def fallback_observer(state: Dict[str, Any]) -> Dict[str, Any]:
    topic_state = state.get("topic_state", {}) if isinstance(state.get("topic_state"), dict) else {}
    topic = topic_state.get("current_topic") or "general"
    return {
        "summary": "Fallback observer: no LLM available.",
        "answer_quality": {"correctness": "unknown", "confidence": "low"},
        "detected_claims": [],
        "skill_updates": [],
        "difficulty_delta": -1,
        "next_action": {
            "type": "clarify",
            "topic": topic,
            "instruction_to_interviewer": "Уточни базовые понятия и задай простой вопрос.",
        },
        "robustness": {
            "off_topic": False,
            "role_reversal": False,
            "hallucination_claim": False,
            "evasive": False,
        },
    }


def fallback_interviewer(state: Dict[str, Any]) -> Dict[str, Any]:
    difficulty = int(state.get("difficulty", 1))
    topic_state = state.get("topic_state", {}) if isinstance(state.get("topic_state"), dict) else {}
    topic = topic_state.get("current_topic") or select_next_topic(state.get("skill_matrix", {}), topic_state)
    candidates = get_candidates(topic, difficulty, None) or get_candidates(None, difficulty, None)
    prompt = candidates[0]["prompt"] if candidates else "Расскажи о своём опыте в разработке."
    return {
        "agent_visible_message": prompt,
        "metadata": {
            "topic": topic,
            "intent": "ask",
            "difficulty": difficulty,
        },
    }


def fallback_factcheck(claim: str) -> Dict[str, Any]:
    return {
        "label": "uncertain",
        "confidence": 50,
        "correction": "Нет подтверждения этому утверждению.",
        "explanation": "Нет достаточных оснований подтвердить или опровергнуть утверждение.",
        "safe_response": "Похоже на спорное утверждение. Давай опираться на базовые знания.",
        "sources": [],
    }


def fallback_final_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
    feedback = {
        "Decision": {"Grade": "Junior", "HiringRecommendation": "No Hire", "ConfidenceScore": 20},
        "HardSkills": {"ConfirmedSkills": [], "KnowledgeGaps": []},
        "SoftSkills": {"Clarity": "Medium", "Honesty": "Medium", "Engagement": "Medium", "Notes": ""},
        "Roadmap": {"NextSteps": [{"topic": "Основы", "why": "Недостаточно данных", "resources": ["Python docs: basics"]}]},
        "Summary": "Недостаточно данных для уверенного решения; требуется дополнительное интервью.",
    }
    return FinalFeedback.model_validate(feedback).model_dump()
