"""Topic selection based on skill matrix and coverage."""
from __future__ import annotations

from typing import Dict, List

from app.policies.question_bank import get_all_topics
from app.policies.context_guard import normalize_topic, should_switch_topic


def _status_priority(status: str) -> int:
    # Lower is higher priority.
    mapping = {
        "gap": 0,
        "uncertain": 1,
        "unknown": 2,
        "confirmed": 3,
    }
    return mapping.get(status, 2)


def select_next_topic(skill_matrix: Dict[str, Dict[str, object]], topic_state: Dict[str, object]) -> str:
    all_topics = get_all_topics()
    last_topics = topic_state.get("last_topics", []) if isinstance(topic_state, dict) else []

    scored: List[tuple[int, str]] = []
    for topic in all_topics:
        entry = skill_matrix.get(topic, {}) if isinstance(skill_matrix, dict) else {}
        status = normalize_topic(str(entry.get("status", "unknown")))
        scored.append((_status_priority(status), topic))

    scored.sort(key=lambda x: x[0])
    selected = scored[0][1] if scored else (all_topics[0] if all_topics else "general")

    if should_switch_topic(last_topics, all_topics):
        for _, topic in scored:
            if topic != last_topics[-1]:
                selected = topic
                break

    return selected

