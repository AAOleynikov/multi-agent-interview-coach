"""Deterministic question bank for policy-driven interviewing."""
from __future__ import annotations

from typing import List, Dict, Optional

QUESTION_BANK: List[Dict[str, object]] = [
    {
        "question_id": "py_types_1",
        "topic": "python_types",
        "difficulty": 1,
        "type": "ask",
        "prompt": "В чём разница между list и tuple в Python? Приведи пример.",
    },
    {
        "question_id": "py_types_1_simplify",
        "topic": "python_types",
        "difficulty": 1,
        "type": "simplify",
        "prompt": "Чем list отличается от tuple?",
    },
    {
        "question_id": "py_types_1_hint",
        "topic": "python_types",
        "difficulty": 1,
        "type": "hint",
        "prompt": "Подсказка: подумай про изменяемость коллекций. Чем list и tuple отличаются?",
    },
    {
        "question_id": "py_iter_2",
        "topic": "python_iterators",
        "difficulty": 2,
        "type": "ask",
        "prompt": "Что такое iterable и iterator? Как работает протокол итерации?",
    },
    {
        "question_id": "py_iter_2_clarify",
        "topic": "python_iterators",
        "difficulty": 2,
        "type": "clarify",
        "prompt": "Уточни разницу между iterable и iterator и как их получить.",
    },
    {
        "question_id": "sql_join_1",
        "topic": "sql_joins",
        "difficulty": 1,
        "type": "ask",
        "prompt": "Что такое JOIN в SQL и какие типы JOIN ты знаешь?",
    },
    {
        "question_id": "sql_join_1_simplify",
        "topic": "sql_joins",
        "difficulty": 1,
        "type": "simplify",
        "prompt": "Объясни простыми словами, что делает JOIN в SQL.",
    },
    {
        "question_id": "py_oop_3",
        "topic": "python_oop",
        "difficulty": 3,
        "type": "ask",
        "prompt": "Объясни разницу между classmethod и staticmethod. Когда их использовать?",
    },
    {
        "question_id": "sql_index_3",
        "topic": "sql_indexes",
        "difficulty": 3,
        "type": "ask",
        "prompt": "Что такое индекс в SQL и какие есть типы индексов?",
    },
    {
        "question_id": "git_rebase_1",
        "topic": "git_basics",
        "difficulty": 1,
        "type": "ask",
        "prompt": "Что делает команда git rebase и когда её используют?",
    },
    {
        "question_id": "git_rebase_1_clarify",
        "topic": "git_basics",
        "difficulty": 1,
        "type": "clarify",
        "prompt": "Когда бы ты выбрал rebase вместо merge?",
    },
]


def get_candidates(topic: Optional[str], difficulty: int, qtype: Optional[str] = None) -> List[Dict[str, object]]:
    candidates = [q for q in QUESTION_BANK if q.get("difficulty") == difficulty]
    if topic:
        candidates = [q for q in candidates if q.get("topic") == topic]
    if qtype:
        candidates = [q for q in candidates if q.get("type") == qtype]
    return candidates


def pick_next_question(asked_questions: set[str], topic: Optional[str], difficulty: int, qtype: str) -> Optional[Dict[str, object]]:
    candidates = get_candidates(topic, difficulty, qtype)
    for q in candidates:
        qid = q.get("question_id")
        if isinstance(qid, str) and qid not in asked_questions:
            return q
    return None


def get_all_topics() -> List[str]:
    topics = sorted({q["topic"] for q in QUESTION_BANK if isinstance(q.get("topic"), str)})
    return topics
