"""Simple JSON logger for interview sessions."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from app.state.schema import InterviewLog, TurnLog


DEFAULT_PARTICIPANT_NAME = "Олейников Антон Александрович"


class InterviewLogger:
    def __init__(self, log_path: str, candidate_profile: Optional[dict] = None):
        self.log_path = log_path
        # Enforce a constant participant name in logs.
        self.participant_name = DEFAULT_PARTICIPANT_NAME
        self.candidate_profile = candidate_profile or {}

    # --- helpers ---------------------------------------------------------
    def _ensure_parent_dir(self) -> None:
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def _save(self, data: Dict[str, Any]) -> None:
        self._ensure_parent_dir()
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- public API ------------------------------------------------------
    def init_log(self) -> None:
        """Create new log if missing; otherwise keep existing content intact."""
        if os.path.exists(self.log_path):
            # Ensure participant_name is always set to the constant value.
            data = self.load()
            try:
                log = InterviewLog.model_validate(data)
                log.participant_name = self.participant_name
                self._save(log.model_dump())
            except Exception:
                # Validate existing file to be safe; will raise if broken.
                self.validate()
            return

        empty_log = InterviewLog(
            participant_name=self.participant_name,
            candidate_profile=self.candidate_profile,
            turns=[],
            final_feedback=None,
        )
        self._save(empty_log.model_dump())

    def append_turn(
        self,
        turn_id: int,
        agent_visible_message: str,
        user_message: str,
        internal_thoughts: str,
    ) -> None:
        data = self.load()
        log = InterviewLog.model_validate(data)

        if log.turns and turn_id <= log.turns[-1].turn_id:
            raise ValueError("turn_id must be greater than the last recorded turn_id")

        new_turn = TurnLog(
            turn_id=turn_id,
            agent_visible_message=agent_visible_message,
            user_message=user_message,
            internal_thoughts=internal_thoughts,
        )
        log.turns.append(new_turn)
        log.participant_name = self.participant_name

        self._save(log.model_dump())

    def set_final_feedback(self, final_feedback) -> None:
        data = self.load()
        log = InterviewLog.model_validate(data)
        log.final_feedback = final_feedback
        log.participant_name = self.participant_name
        self._save(log.model_dump())

    def set_candidate_profile(self, candidate_profile: dict) -> None:
        data = self.load()
        log = InterviewLog.model_validate(data)
        log.candidate_profile = candidate_profile
        log.participant_name = self.participant_name
        self._save(log.model_dump())

    def load(self) -> Dict[str, Any]:
        with open(self.log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self) -> None:
        """Raise if the current log file does not match InterviewLog schema."""
        InterviewLog.model_validate(self.load())
