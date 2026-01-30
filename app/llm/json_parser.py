"""Robust JSON parsing and schema validation utilities."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type

from app.llm.schemas import BaseModel, ValidationError


class JsonSchemaValidationError(Exception):
    def __init__(
        self,
        message: str,
        original_text: str,
        validation_error: Exception,
        repaired_text: Optional[str] = None,
    ):
        super().__init__(message)
        self.original_text = original_text
        self.validation_error = validation_error
        self.repaired_text = repaired_text


def _extract_json_substring(text: str) -> str:
    """Extract a JSON object substring from arbitrary LLM text.

    Strategy:
    1) Try parsing the full text as JSON directly.
    2) Fallback: find the first '{' and last '}' and attempt to parse.
    3) Fallback: walk the string to find the first balanced JSON object.
    """
    text = text.strip()

    # Try direct parse
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Simple slice between first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    # Balanced brace scanning
    depth = 0
    start_idx = None
    for idx, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start_idx = idx
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start_idx is not None:
                    candidate = text[start_idx : idx + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except Exception:
                        start_idx = None  # keep scanning
    raise ValueError("Unable to extract JSON object from text")


def parse_json_with_schema(text: str, schema: Type[BaseModel]) -> BaseModel:
    """Parse arbitrary text into JSON and validate against a schema."""
    try:
        json_str = _extract_json_substring(text)
        data = json.loads(json_str)
        return schema.model_validate(data)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise JsonSchemaValidationError(
            message=f"Failed to parse or validate JSON: {exc}",
            original_text=text,
            validation_error=exc,
        ) from exc


def _schema_to_json(schema: Type[BaseModel]) -> str:
    try:
        schema_dict = schema.model_json_schema()
    except Exception:
        schema_dict = {"title": schema.__name__}
    return json.dumps(schema_dict, ensure_ascii=False, indent=2)


def _convert_messages(messages: list[Dict[str, Any]]):
    """Convert simple role/content dicts to LangChain messages when available."""
    try:
        from langchain.schema import SystemMessage, HumanMessage, AIMessage
    except Exception:  # pragma: no cover - fallback
        return messages

    converted = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted


def repair_to_valid_json(llm, bad_text: str, schema_json: str) -> str:
    """Ask the LLM to rewrite its response into valid JSON only."""
    try:
        from langchain.schema import SystemMessage, HumanMessage
    except Exception:  # pragma: no cover - minimal fallback
        SystemMessage = None
        HumanMessage = None

    instruction = (
        "Ты вернул невалидный JSON. Верни только валидный JSON, строго по схеме. "
        "Никакого текста до или после. Никакого markdown."
    )

    if SystemMessage and HumanMessage:
        messages = [
            SystemMessage(content=instruction),
            HumanMessage(
                content=f"Schema:\n{schema_json}\n\nBad JSON:\n{bad_text}\n\nОтвет:"
            ),
        ]
    else:
        messages = [
            {"role": "system", "content": instruction},
            {
                "role": "user",
                "content": f"Schema:\n{schema_json}\n\nBad JSON:\n{bad_text}\n\nОтвет:",
            },
        ]

    response = llm.invoke(messages) if hasattr(llm, "invoke") else llm(messages)  # type: ignore
    content = getattr(response, "content", None) if response is not None else None
    if content is None and isinstance(response, str):
        content = response
    if content is None:
        raise ValueError("LLM repair step returned empty response")
    return content.strip()


def call_llm_for_json(llm, messages: list[Dict[str, Any]], schema: Type[BaseModel], max_attempts: int = 2) -> BaseModel:
    """Call LLM, parse JSON, optionally repair once on failure."""
    last_error: Optional[JsonSchemaValidationError] = None

    converted_messages = _convert_messages(messages)

    for attempt in range(max_attempts):
        response = llm.invoke(converted_messages) if hasattr(llm, "invoke") else llm(converted_messages)  # type: ignore
        content = getattr(response, "content", None) if response is not None else None
        if content is None and isinstance(response, str):
            content = response
        if content is None:
            raise JsonSchemaValidationError(
                message="LLM returned empty content",
                original_text=str(response),
                validation_error=ValueError("empty content"),
            )

        try:
            return parse_json_with_schema(content, schema)
        except JsonSchemaValidationError as exc:
            last_error = exc
            if attempt == max_attempts - 1:
                break
            repaired = repair_to_valid_json(llm, content, _schema_to_json(schema))
            try:
                return parse_json_with_schema(repaired, schema)
            except JsonSchemaValidationError as exc_repaired:
                last_error = JsonSchemaValidationError(
                    message=str(exc_repaired),
                    original_text=content,
                    validation_error=exc_repaired.validation_error,
                    repaired_text=repaired,
                )
                break

    assert last_error is not None  # for type checkers
    raise last_error
