"""Factory for OpenAI-compatible chat models via LangChain."""
from __future__ import annotations

from typing import Any, Dict

from app.config import settings

# Role configuration: model env var name and default temperature.
ROLE_CONFIG = {
    "interviewer": {"model_attr": "model_interviewer", "temperature": 0.6},
    "observer": {"model_attr": "model_observer", "temperature": 0.2},
    "factchecker": {"model_attr": "model_factchecker", "temperature": 0.1},
    "hiring_manager": {"model_attr": "model_hiring_manager", "temperature": 0.2},
    "stop_intent": {"model_attr": "model_stop_intent", "temperature": 0.0, "max_tokens": 200, "timeout": 15},
    "profile_extractor": {"model_attr": "model_profile_extractor", "temperature": 0.0, "max_tokens": 200, "timeout": 20},
}


def _import_chat_openai():
    """Support both new (langchain_openai) and legacy imports."""
    try:  # langchain-openai package
        from langchain_openai import ChatOpenAI  # type: ignore
        return ChatOpenAI, "new"
    except Exception:
        pass
    try:  # legacy langchain
        from langchain.chat_models import ChatOpenAI  # type: ignore
        return ChatOpenAI, "legacy"
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "LangChain ChatOpenAI is not installed. Install 'langchain-openai' or 'langchain'."
        ) from exc


def get_chat_model(role: str):
    role_key = role.lower()
    if role_key not in ROLE_CONFIG:
        raise ValueError(f"Unknown role '{role}'. Expected one of {list(ROLE_CONFIG)}")

    ChatOpenAI, flavor = _import_chat_openai()

    conf = ROLE_CONFIG[role_key]
    model_name = getattr(settings, conf["model_attr"], None)
    if role_key == "profile_extractor" and not model_name:
        model_name = settings.model_stop_intent
    temperature = conf["temperature"]

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    if not settings.openai_base_url:
        raise RuntimeError("OPENAI_BASE_URL is not set")
    if not model_name:
        raise RuntimeError(f"Model for role '{role}' is not configured in environment")

    common_kwargs: Dict[str, Any] = {
        "model": model_name,
        "max_retries": settings.default_max_retries,
    }
    # Some models (e.g., o-series) only support default temperature=1.
    if not model_name.lower().startswith("o"):
        common_kwargs["temperature"] = temperature

    # Align parameter names across flavors
    if flavor == "new":
        common_kwargs.update({
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
            "timeout": settings.default_timeout_s,
        })
        if "timeout" in conf:
            common_kwargs["timeout"] = conf["timeout"]
        if "max_tokens" in conf:
            common_kwargs["max_tokens"] = conf["max_tokens"]
        return ChatOpenAI(**common_kwargs)

    # legacy
    common_kwargs.update({
        "openai_api_key": settings.openai_api_key,
        "openai_api_base": settings.openai_base_url,
        "request_timeout": settings.default_timeout_s,
    })
    if "timeout" in conf:
        common_kwargs["request_timeout"] = conf["timeout"]
    if "max_tokens" in conf:
        common_kwargs["max_tokens"] = conf["max_tokens"]
    return ChatOpenAI(**common_kwargs)
