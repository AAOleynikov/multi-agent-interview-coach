"""LLM-based candidate profile extractor."""
from __future__ import annotations

import json
import os
from typing import Dict

from app.llm.client import get_chat_model
from app.llm.retry import safe_call_for_json, LLMCallError
from app.llm.schemas import CandidateProfileOutput
from app.logging.errors import log_error

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "profile_extractor.md")

_LEVEL_MAP = {
    "intern": "Intern",
    "junior": "Junior",
    "jr": "Junior",
    "middle": "Middle",
    "mid": "Middle",
    "senior": "Senior",
    "sr": "Senior",
    "lead": "Lead",
    "unknown": "Unknown",
}


def _normalize_level(level: str) -> str:
    key = (level or "").strip().lower()
    return _LEVEL_MAP.get(key, level or "Unknown")


def _normalize_skills(skills: list) -> list:
    normalized = []
    seen = set()
    for skill in skills or []:
        if not isinstance(skill, str):
            continue
        s = skill.strip()
        if not s:
            continue
        s_norm = s.lower()
        mapping = {
            "python": "Python",
            "c++": "C++",
            "cpp": "C++",
            "c#": "C#",
            "sql": "SQL",
            "git": "Git",
            "qt": "Qt",
            "django": "Django",
        }
        s = mapping.get(s_norm, s)
        if s_norm not in seen:
            normalized.append(s)
            seen.add(s_norm)
    return normalized


def _strip_level_from_position(position: str, level: str) -> str:
    pos = position or ""
    lvl = (level or "").strip()
    if not lvl:
        return pos.strip()
    lowered = pos.lower().replace(lvl.lower(), "").strip()
    return " ".join(lowered.split()) or pos.strip()


def extract_candidate_profile_llm(text: str) -> Dict[str, object]:
    llm = get_chat_model("profile_extractor")

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps({"text": text}, ensure_ascii=False)},
    ]

    try:
        output = safe_call_for_json(
            llm,
            messages,
            CandidateProfileOutput,
            max_attempts=2,
            timeout_s=20,
            role="profile_extractor",
        )
    except LLMCallError as exc:
        log_error("unknown", "profile_extractor", exc)
        output = CandidateProfileOutput.model_validate(
            {
                "name": "",
                "level": "Unknown",
                "position": "",
                "skills": [],
                "confidence": {},
                "assumptions": ["LLM extraction failed"],
            }
        )

    data = output.model_dump()
    data["level"] = _normalize_level(data.get("level"))
    data["skills"] = _normalize_skills(data.get("skills", []))
    data["position"] = _strip_level_from_position(data.get("position", ""), data.get("level", ""))
    return data
