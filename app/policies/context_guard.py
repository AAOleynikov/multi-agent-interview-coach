"""Context-aware guards against repetition and topic loops."""
from __future__ import annotations

from typing import Dict, List, Optional


def normalize_topic(topic: str) -> str:
    return (topic or "").strip().lower()


def enforce_no_repeat(chosen: Optional[Dict[str, object]], asked_questions: set[str], fallback_pool: List[Dict[str, object]]) -> Optional[Dict[str, object]]:
    if chosen is None:
        for candidate in fallback_pool:
            qid = candidate.get("question_id")
            if isinstance(qid, str) and qid not in asked_questions:
                return candidate
        return None

    qid = chosen.get("question_id")
    if isinstance(qid, str) and qid not in asked_questions:
        return chosen

    for candidate in fallback_pool:
        fallback_id = candidate.get("question_id")
        if isinstance(fallback_id, str) and fallback_id not in asked_questions:
            return candidate
    return None


def should_switch_topic(last_topics: List[str], available_topics: List[str]) -> bool:
    if len(last_topics) < 2:
        return False
    if last_topics[-1] != last_topics[-2]:
        return False
    return any(topic != last_topics[-1] for topic in available_topics)
