"""Application configuration for LLM access and defaults.

The module is dependency-light: it attempts to load a local .env if python-dotenv
is available, otherwise falls back to environment variables only.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:  # Optional: load .env if the package is present.
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv()


@dataclass
class Settings:
    openai_api_key: Optional[str] = os.environ.get("OPENAI_API_KEY")
    openai_base_url: Optional[str] = os.environ.get("OPENAI_BASE_URL")

    model_interviewer: Optional[str] = os.environ.get("OPENAI_MODEL_INTERVIEWER")
    model_observer: Optional[str] = os.environ.get("OPENAI_MODEL_OBSERVER")
    model_factchecker: Optional[str] = os.environ.get("OPENAI_MODEL_FACTCHECKER")
    model_hiring_manager: Optional[str] = os.environ.get("OPENAI_MODEL_HIRING_MANAGER")
    model_stop_intent: Optional[str] = os.environ.get("OPENAI_MODEL_STOP_INTENT")
    model_profile_extractor: Optional[str] = os.environ.get("OPENAI_MODEL_PROFILE_EXTRACTOR")

    default_timeout_s: float = float(os.environ.get("DEFAULT_TIMEOUT_S", 60))
    default_max_retries: int = int(os.environ.get("DEFAULT_MAX_RETRIES", 2))


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
