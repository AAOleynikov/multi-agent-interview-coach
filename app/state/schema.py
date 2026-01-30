"""State and logging schemas for interview sessions.

This module deliberately avoids external dependencies so it can run in
restricted environments while still performing basic validation that mirrors
Pydantic's behaviour used later in the project.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from uuid import UUID


class CandidateProfile:
    def __init__(
        self,
        name: Optional[str],
        level: str,
        position: str,
        skills: List[str],
        confidence: Optional[Dict[str, Any]] = None,
        assumptions: Optional[List[str]] = None,
    ):
        self._assert_type("name", name, (str, type(None)))
        self._assert_type("level", level, str)
        self._assert_type("position", position, str)
        self._assert_type("skills", skills, list)
        if confidence is not None:
            self._assert_type("confidence", confidence, dict)
        if assumptions is not None:
            self._assert_type("assumptions", assumptions, list)

        self.name = name
        self.level = level
        self.position = position
        self.skills = skills
        self.confidence = confidence or {}
        self.assumptions = assumptions or []

    # --- helpers -----------------------------------------------------
    @staticmethod
    def _assert_type(field: str, value: Any, expected_type) -> None:
        if not isinstance(value, expected_type):
            raise ValueError(f"{field} must be of type {expected_type}")

    # --- Pydantic-like API ------------------------------------------
    @classmethod
    def model_validate(cls, data: Any) -> "CandidateProfile":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValueError("CandidateProfile expects a mapping")
        name = data.get("name")
        level = data.get("level") or "Unknown"
        position = data.get("position") or ""
        skills = data.get("skills") or []
        confidence = data.get("confidence")
        assumptions = data.get("assumptions")
        return cls(
            name=name,
            level=level,
            position=position,
            skills=skills,
            confidence=confidence,
            assumptions=assumptions,
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "position": self.position,
            "skills": list(self.skills),
            "confidence": self.confidence,
            "assumptions": list(self.assumptions),
        }


class TurnLog:
    def __init__(
        self,
        turn_id: int,
        agent_visible_message: str,
        user_message: str,
        internal_thoughts: str,
    ):
        self._assert_type("turn_id", turn_id, int)
        self._assert_type("agent_visible_message", agent_visible_message, str)
        self._assert_type("user_message", user_message, str)
        self._assert_type("internal_thoughts", internal_thoughts, str)

        if not internal_thoughts.strip():
            raise ValueError("internal_thoughts must be a non-empty string")

        self.turn_id = turn_id
        self.agent_visible_message = agent_visible_message
        self.user_message = user_message
        self.internal_thoughts = internal_thoughts

    @staticmethod
    def _assert_type(field: str, value: Any, expected_type) -> None:
        if not isinstance(value, expected_type):
            raise ValueError(f"{field} must be of type {expected_type}")

    @classmethod
    def model_validate(cls, data: Any) -> "TurnLog":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValueError("TurnLog expects a mapping")
        required_fields = ["turn_id", "agent_visible_message", "user_message", "internal_thoughts"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"TurnLog missing fields: {', '.join(missing)}")
        return cls(
            turn_id=data["turn_id"],
            agent_visible_message=data["agent_visible_message"],
            user_message=data["user_message"],
            internal_thoughts=data["internal_thoughts"],
        )

    def model_dump(self) -> Dict[str, Any]:
        payload = {
            "turn_id": self.turn_id,
            "agent_visible_message": self.agent_visible_message,
            "user_message": self.user_message,
            "internal_thoughts": self.internal_thoughts,
        }
        return payload


class InterviewLog:
    def __init__(
        self,
        participant_name: str,
        candidate_profile: Dict[str, Any],
        turns: List[TurnLog],
        final_feedback: Optional[Union[str, Dict[str, Any]]] = None,
    ):
        self._assert_type("participant_name", participant_name, str)
        self._assert_type("candidate_profile", candidate_profile, dict)
        self._assert_type("turns", turns, list)
        for t in turns:
            if not isinstance(t, TurnLog):
                raise ValueError("each turn must be a TurnLog instance")
        if final_feedback is not None and not isinstance(final_feedback, (str, dict)):
            raise ValueError("final_feedback must be str, dict or None")

        self.participant_name = participant_name
        self.candidate_profile = candidate_profile
        self.turns = turns
        self.final_feedback = final_feedback

    @staticmethod
    def _assert_type(field: str, value: Any, expected_type) -> None:
        if not isinstance(value, expected_type):
            raise ValueError(f"{field} must be of type {expected_type}")

    @classmethod
    def model_validate(cls, data: Any) -> "InterviewLog":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValueError("InterviewLog expects a mapping")
        if "participant_name" not in data:
            raise ValueError("participant_name is required")
        if "candidate_profile" not in data:
            raise ValueError("candidate_profile is required")
        turns_raw = data.get("turns", [])
        if not isinstance(turns_raw, list):
            raise ValueError("turns must be a list")
        turns = [TurnLog.model_validate(t) for t in turns_raw]
        final_feedback = data.get("final_feedback")
        return cls(
            participant_name=data["participant_name"],
            candidate_profile=data["candidate_profile"],
            turns=turns,
            final_feedback=final_feedback,
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "participant_name": self.participant_name,
            "candidate_profile": self.candidate_profile,
            "turns": [t.model_dump() for t in self.turns],
            "final_feedback": self.final_feedback,
        }


class InterviewState:
    def __init__(
        self,
        session_id: str,
        turn_id: int,
        candidate_profile: CandidateProfile,
        history: List[Dict[str, Any]],
        log_path: str,
        topic_state: Optional[Dict[str, Any]] = None,
        last_question_id: Optional[str] = None,
        planned_question: Optional[Dict[str, Any]] = None,
        planned_response: Optional[Dict[str, Any]] = None,
        action_type: Optional[str] = None,
    ):
        self._assert_type("session_id", session_id, str)
        self._assert_type("turn_id", turn_id, int)
        self._assert_type("candidate_profile", candidate_profile, CandidateProfile)
        self._assert_type("history", history, list)
        self._assert_type("log_path", log_path, str)
        if topic_state is not None:
            self._assert_type("topic_state", topic_state, dict)
        if last_question_id is not None:
            self._assert_type("last_question_id", last_question_id, str)
        if planned_question is not None:
            self._assert_type("planned_question", planned_question, dict)
        if planned_response is not None:
            self._assert_type("planned_response", planned_response, dict)
        if action_type is not None:
            self._assert_type("action_type", action_type, str)

        # Validate UUID format for session_id.
        try:
            UUID(hex=session_id)
        except Exception as exc:
            raise ValueError("session_id must be a valid UUID hex string") from exc

        self.session_id = session_id
        self.turn_id = turn_id
        self.candidate_profile = candidate_profile
        self.history = history
        self.log_path = log_path
        self.topic_state = topic_state or {"current_topic": None, "last_topics": [], "coverage": {}}
        self.last_question_id = last_question_id
        self.planned_question = planned_question
        self.planned_response = planned_response
        self.action_type = action_type

    @staticmethod
    def _assert_type(field: str, value: Any, expected_type) -> None:
        if not isinstance(value, expected_type):
            raise ValueError(f"{field} must be of type {expected_type}")

    @classmethod
    def model_validate(cls, data: Any) -> "InterviewState":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise ValueError("InterviewState expects a mapping")

        candidate_profile = CandidateProfile.model_validate(data.get("candidate_profile"))
        history = data.get("history") if "history" in data else []
        if history is None:
            history = []
        if not isinstance(history, list):
            raise ValueError("history must be a list")

        return cls(
            session_id=data.get("session_id"),
            turn_id=data.get("turn_id", 0),
            candidate_profile=candidate_profile,
            history=history,
            log_path=data.get("log_path"),
            topic_state=data.get("topic_state"),
            last_question_id=data.get("last_question_id"),
            planned_question=data.get("planned_question"),
            planned_response=data.get("planned_response"),
            action_type=data.get("action_type"),
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "candidate_profile": self.candidate_profile.model_dump(),
            "history": self.history,
            "log_path": self.log_path,
            "topic_state": self.topic_state,
            "last_question_id": self.last_question_id,
            "planned_question": self.planned_question,
            "planned_response": self.planned_response,
            "action_type": self.action_type,
        }
