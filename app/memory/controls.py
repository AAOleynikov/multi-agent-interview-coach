"""Context controls: history windowing and loop guards."""
from __future__ import annotations

import hashlib
from typing import List, Dict

from app.policies.topic_manager import select_next_topic


def history_tail(history: List[Dict[str, str]], max_items: int = 16) -> List[Dict[str, str]]:
    if not history:
        return []
    return history[-max_items:]


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha1(prompt.encode("utf-8")).hexdigest()


def detect_loop(topic_state: dict, new_prompt: str) -> bool:
    hashes = topic_state.get("last_prompts_hashes", []) if isinstance(topic_state.get("last_prompts_hashes"), list) else []
    new_hash = _hash_prompt(new_prompt or "")
    hashes.append(new_hash)
    topic_state["last_prompts_hashes"] = hashes[-5:]
    if len(hashes) >= 3 and len(set(hashes[-3:])) == 1:
        return True
    return False


def break_loop(skill_matrix: dict, topic_state: dict) -> str:
    return select_next_topic(skill_matrix, topic_state)
