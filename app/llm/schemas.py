"""Pydantic-like schemas for LLM JSON outputs.

We attempt to import real Pydantic when available. In offline or minimal
environments we fall back to a lightweight validator that mimics the
``model_validate`` / ``model_dump`` interface required by the JSON pipeline.
"""
from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    from pydantic import BaseModel, ValidationError  # type: ignore
except ImportError:  # Lightweight fallback

    class ValidationError(ValueError):
        pass

    class BaseModel:
        """Minimal stand-in for Pydantic's BaseModel."""

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        @classmethod
        def model_validate(cls, data: Any):
            if not isinstance(data, dict):
                raise ValidationError("data must be a mapping")
            return cls(**data)

        def model_dump(self) -> Dict[str, Any]:
            return self.__dict__

        def model_dump_json(self) -> str:
            return json.dumps(self.model_dump(), ensure_ascii=False)

        @classmethod
        def model_json_schema(cls) -> Dict[str, Any]:
            return {"title": cls.__name__}

        class Config:
            validate_assignment = False



class Robustness(BaseModel):
    off_topic: bool
    role_reversal: bool
    hallucination_claim: bool
    evasive: bool

    @classmethod
    def model_validate(cls, data: Any) -> "Robustness":
        if not isinstance(data, dict):
            raise ValidationError("robustness must be an object")
        required = ["off_topic", "role_reversal", "hallucination_claim", "evasive"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"robustness missing fields: {', '.join(missing)}")
        for k in required:
            if not isinstance(data[k], bool):
                raise ValidationError(f"robustness.{k} must be a boolean")
        return cls(**{k: data[k] for k in required})

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {k: {"type": "boolean"} for k in [
                "off_topic",
                "role_reversal",
                "hallucination_claim",
                "evasive",
            ]},
            "required": [
                "off_topic",
                "role_reversal",
                "hallucination_claim",
                "evasive",
            ],
        }


class NextAction(BaseModel):
    type: str
    instruction_to_interviewer: str

    @classmethod
    def model_validate(cls, data: Any) -> "NextAction":
        if not isinstance(data, dict):
            raise ValidationError("next_action must be an object")
        if "type" not in data or "instruction_to_interviewer" not in data:
            raise ValidationError("next_action requires 'type' and 'instruction_to_interviewer'")
        if not isinstance(data["type"], str):
            raise ValidationError("next_action.type must be a string")
        if not isinstance(data["instruction_to_interviewer"], str):
            raise ValidationError("next_action.instruction_to_interviewer must be a string")
        return cls(type=data["type"], instruction_to_interviewer=data["instruction_to_interviewer"])

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "instruction_to_interviewer": {"type": "string"},
            },
            "required": ["type", "instruction_to_interviewer"],
        }


class RobustnessFlags(BaseModel):
    off_topic: bool
    role_reversal: bool
    hallucination_claim: bool
    evasive: bool

    @classmethod
    def model_validate(cls, data: Any) -> "RobustnessFlags":
        if not isinstance(data, dict):
            raise ValidationError("robustness must be an object")
        required = ["off_topic", "role_reversal", "hallucination_claim", "evasive"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"robustness missing fields: {', '.join(missing)}")
        for k in required:
            if not isinstance(data[k], bool):
                raise ValidationError(f"robustness.{k} must be a boolean")
        return cls(**{k: data[k] for k in required})

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {k: {"type": "boolean"} for k in [
                "off_topic",
                "role_reversal",
                "hallucination_claim",
                "evasive",
            ]},
            "required": [
                "off_topic",
                "role_reversal",
                "hallucination_claim",
                "evasive",
            ],
        }


class ObserverNextAction(BaseModel):
    type: str
    topic: str
    instruction_to_interviewer: str

    @classmethod
    def model_validate(cls, data: Any) -> "ObserverNextAction":
        if not isinstance(data, dict):
            raise ValidationError("next_action must be an object")
        required = ["type", "topic", "instruction_to_interviewer"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"next_action missing fields: {', '.join(missing)}")
        if not isinstance(data["type"], str):
            raise ValidationError("next_action.type must be a string")
        if not isinstance(data["topic"], str):
            raise ValidationError("next_action.topic must be a string")
        if not isinstance(data["instruction_to_interviewer"], str) or not data["instruction_to_interviewer"].strip():
            raise ValidationError("next_action.instruction_to_interviewer must be a non-empty string")
        return cls(
            type=data["type"],
            topic=data["topic"],
            instruction_to_interviewer=data["instruction_to_interviewer"],
        )

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "topic": {"type": "string"},
                "instruction_to_interviewer": {"type": "string"},
            },
            "required": ["type", "topic", "instruction_to_interviewer"],
        }


class SkillUpdate(BaseModel):
    topic: str
    status: str
    evidence: str

    @classmethod
    def model_validate(cls, data: Any) -> "SkillUpdate":
        if not isinstance(data, dict):
            raise ValidationError("skill_updates entries must be objects")
        required = ["topic", "status", "evidence"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"skill_update missing fields: {', '.join(missing)}")
        if not isinstance(data["topic"], str):
            raise ValidationError("skill_update.topic must be a string")
        if not isinstance(data["status"], str):
            raise ValidationError("skill_update.status must be a string")
        if not isinstance(data["evidence"], str):
            raise ValidationError("skill_update.evidence must be a string")
        return cls(topic=data["topic"], status=data["status"], evidence=data["evidence"])

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "status": {"type": "string"},
                "evidence": {"type": "string"},
            },
            "required": ["topic", "status", "evidence"],
        }


class ObserverOutput(BaseModel):
    summary: str
    answer_quality: Dict[str, Any]
    detected_claims: list
    skill_updates: list
    difficulty_delta: int
    next_action: ObserverNextAction
    robustness: RobustnessFlags

    @classmethod
    def model_validate(cls, data: Any) -> "ObserverOutput":
        if not isinstance(data, dict):
            raise ValidationError("output must be an object")
        required = [
            "summary",
            "answer_quality",
            "detected_claims",
            "skill_updates",
            "difficulty_delta",
            "next_action",
            "robustness",
        ]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"missing fields: {', '.join(missing)}")

        summary = data["summary"]
        if not isinstance(summary, str):
            raise ValidationError("summary must be a string")

        difficulty_delta = data["difficulty_delta"]
        if not isinstance(difficulty_delta, int):
            raise ValidationError("difficulty_delta must be an integer")
        if difficulty_delta < -2 or difficulty_delta > 2:
            raise ValidationError("difficulty_delta must be between -2 and 2")

        if not isinstance(data["answer_quality"], dict):
            raise ValidationError("answer_quality must be an object")
        if not isinstance(data["detected_claims"], list):
            raise ValidationError("detected_claims must be a list")
        if not isinstance(data["skill_updates"], list):
            raise ValidationError("skill_updates must be a list")

        skill_updates = [SkillUpdate.model_validate(item) for item in data["skill_updates"]]
        next_action = ObserverNextAction.model_validate(data["next_action"])
        robustness = RobustnessFlags.model_validate(data["robustness"])

        return cls(
            summary=summary,
            answer_quality=data["answer_quality"],
            detected_claims=data["detected_claims"],
            skill_updates=skill_updates,
            difficulty_delta=difficulty_delta,
            next_action=next_action,
            robustness=robustness,
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "answer_quality": self.answer_quality,
            "detected_claims": self.detected_claims,
            "skill_updates": [item.model_dump() for item in self.skill_updates],
            "difficulty_delta": self.difficulty_delta,
            "next_action": self.next_action.model_dump(),
            "robustness": self.robustness.model_dump(),
        }

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "answer_quality": {"type": "object"},
                "detected_claims": {"type": "array"},
                "skill_updates": {"type": "array"},
                "difficulty_delta": {"type": "integer", "minimum": -2, "maximum": 2},
                "next_action": ObserverNextAction.model_json_schema(),
                "robustness": RobustnessFlags.model_json_schema(),
            },
            "required": [
                "summary",
                "answer_quality",
                "detected_claims",
                "skill_updates",
                "difficulty_delta",
                "next_action",
                "robustness",
            ],
        }


class InterviewerMetadata(BaseModel):
    topic: str
    intent: str
    difficulty: int

    @classmethod
    def model_validate(cls, data: Any) -> "InterviewerMetadata":
        if not isinstance(data, dict):
            raise ValidationError("metadata must be an object")
        required = ["topic", "intent", "difficulty"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"metadata missing fields: {', '.join(missing)}")
        if not isinstance(data["topic"], str):
            raise ValidationError("metadata.topic must be a string")
        if not isinstance(data["intent"], str):
            raise ValidationError("metadata.intent must be a string")
        if not isinstance(data["difficulty"], int):
            raise ValidationError("metadata.difficulty must be an integer")
        if data["difficulty"] < 1 or data["difficulty"] > 5:
            raise ValidationError("metadata.difficulty must be between 1 and 5")
        return cls(topic=data["topic"], intent=data["intent"], difficulty=data["difficulty"])

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "intent": {"type": "string"},
                "difficulty": {"type": "integer", "minimum": 1, "maximum": 5},
            },
            "required": ["topic", "intent", "difficulty"],
        }


class InterviewerOutput(BaseModel):
    agent_visible_message: str
    metadata: InterviewerMetadata

    @classmethod
    def model_validate(cls, data: Any) -> "InterviewerOutput":
        if not isinstance(data, dict):
            raise ValidationError("output must be an object")
        required = ["agent_visible_message", "metadata"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"missing fields: {', '.join(missing)}")
        message = data["agent_visible_message"]
        if not isinstance(message, str):
            raise ValidationError("agent_visible_message must be a string")
        if len(message.strip()) < 10 or len(message) > 1200:
            raise ValidationError("agent_visible_message must be 10..1200 characters")
        metadata = InterviewerMetadata.model_validate(data["metadata"])
        return cls(agent_visible_message=message, metadata=metadata)

    def model_dump(self) -> Dict[str, Any]:
        return {
            "agent_visible_message": self.agent_visible_message,
            "metadata": self.metadata.model_dump(),
        }

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agent_visible_message": {"type": "string"},
                "metadata": InterviewerMetadata.model_json_schema(),
            },
            "required": ["agent_visible_message", "metadata"],
        }


class FactCheckVerdict(BaseModel):
    label: str
    confidence: int
    correction: str
    explanation: str
    safe_response: str
    sources: list

    @classmethod
    def model_validate(cls, data: Any) -> "FactCheckVerdict":
        if not isinstance(data, dict):
            raise ValidationError("output must be an object")
        required = ["label", "confidence", "correction", "explanation", "safe_response"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"missing fields: {', '.join(missing)}")
        label = data["label"]
        if not isinstance(label, str) or label not in {"true", "false", "uncertain", "misleading"}:
            raise ValidationError("label must be one of true|false|uncertain|misleading")
        confidence = data["confidence"]
        if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
            raise ValidationError("confidence must be between 0 and 100")
        correction = data["correction"]
        explanation = data["explanation"]
        safe_response = data["safe_response"]
        if not isinstance(correction, str):
            raise ValidationError("correction must be a string")
        if not isinstance(explanation, str):
            raise ValidationError("explanation must be a string")
        if not isinstance(safe_response, str) or not safe_response.strip():
            raise ValidationError("safe_response must be a non-empty string")
        sources = data.get("sources", [])
        if sources is None:
            sources = []
        if not isinstance(sources, list):
            raise ValidationError("sources must be a list")
        return cls(
            label=label,
            confidence=confidence,
            correction=correction,
            explanation=explanation,
            safe_response=safe_response,
            sources=sources,
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "correction": self.correction,
            "explanation": self.explanation,
            "safe_response": self.safe_response,
            "sources": list(self.sources),
        }

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)

    @classmethod
    def model_json_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "label": {"type": "string", "enum": ["true", "false", "uncertain", "misleading"]},
                "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                "correction": {"type": "string"},
                "explanation": {"type": "string"},
                "safe_response": {"type": "string"},
                "sources": {"type": "array"},
            },
            "required": ["label", "confidence", "correction", "explanation", "safe_response"],
        }


class DecisionBlock(BaseModel):
    Grade: str
    HiringRecommendation: str
    ConfidenceScore: int

    @classmethod
    def model_validate(cls, data: Any) -> "DecisionBlock":
        if not isinstance(data, dict):
            raise ValidationError("Decision must be an object")
        required = ["Grade", "HiringRecommendation", "ConfidenceScore"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"Decision missing fields: {', '.join(missing)}")
        grade = data["Grade"]
        if not isinstance(grade, str) or grade not in {"Junior", "Middle", "Senior"}:
            raise ValidationError("Decision.Grade must be Junior|Middle|Senior")
        rec = data["HiringRecommendation"]
        if not isinstance(rec, str) or rec not in {"Hire", "No Hire", "Strong Hire"}:
            raise ValidationError("Decision.HiringRecommendation must be Hire|No Hire|Strong Hire")
        score = data["ConfidenceScore"]
        if not isinstance(score, int) or score < 0 or score > 100:
            raise ValidationError("Decision.ConfidenceScore must be 0..100")
        return cls(Grade=grade, HiringRecommendation=rec, ConfidenceScore=score)

    def model_dump(self) -> Dict[str, Any]:
        return {
            "Grade": self.Grade,
            "HiringRecommendation": self.HiringRecommendation,
            "ConfidenceScore": self.ConfidenceScore,
        }


class HardSkillsBlock(BaseModel):
    ConfirmedSkills: list
    KnowledgeGaps: list

    @classmethod
    def model_validate(cls, data: Any) -> "HardSkillsBlock":
        if not isinstance(data, dict):
            raise ValidationError("HardSkills must be an object")
        confirmed = data.get("ConfirmedSkills", [])
        gaps = data.get("KnowledgeGaps", [])
        if not isinstance(confirmed, list):
            raise ValidationError("ConfirmedSkills must be a list")
        if not isinstance(gaps, list):
            raise ValidationError("KnowledgeGaps must be a list")
        for gap in gaps:
            if not isinstance(gap, dict):
                raise ValidationError("KnowledgeGaps entries must be objects")
            if not gap.get("correct_answer") or not isinstance(gap.get("correct_answer"), str):
                raise ValidationError("KnowledgeGaps.correct_answer must be a non-empty string")
        return cls(ConfirmedSkills=confirmed, KnowledgeGaps=gaps)

    def model_dump(self) -> Dict[str, Any]:
        return {
            "ConfirmedSkills": list(self.ConfirmedSkills),
            "KnowledgeGaps": list(self.KnowledgeGaps),
        }


class SoftSkillsBlock(BaseModel):
    Clarity: str
    Honesty: str
    Engagement: str
    Notes: str

    @classmethod
    def model_validate(cls, data: Any) -> "SoftSkillsBlock":
        if not isinstance(data, dict):
            raise ValidationError("SoftSkills must be an object")
        for field in ["Clarity", "Honesty", "Engagement", "Notes"]:
            if field not in data:
                raise ValidationError(f"SoftSkills missing field {field}")
        for field in ["Clarity", "Honesty", "Engagement"]:
            val = data[field]
            if not isinstance(val, str) or val not in {"Low", "Medium", "High"}:
                raise ValidationError(f"SoftSkills.{field} must be Low|Medium|High")
        if not isinstance(data["Notes"], str):
            raise ValidationError("SoftSkills.Notes must be a string")
        return cls(
            Clarity=data["Clarity"],
            Honesty=data["Honesty"],
            Engagement=data["Engagement"],
            Notes=data["Notes"],
        )

    def model_dump(self) -> Dict[str, Any]:
        return {
            "Clarity": self.Clarity,
            "Honesty": self.Honesty,
            "Engagement": self.Engagement,
            "Notes": self.Notes,
        }


class RoadmapBlock(BaseModel):
    NextSteps: list

    @classmethod
    def model_validate(cls, data: Any) -> "RoadmapBlock":
        if not isinstance(data, dict):
            raise ValidationError("Roadmap must be an object")
        steps = data.get("NextSteps", [])
        if not isinstance(steps, list):
            raise ValidationError("Roadmap.NextSteps must be a list")
        return cls(NextSteps=steps)

    def model_dump(self) -> Dict[str, Any]:
        return {"NextSteps": list(self.NextSteps)}


class FinalFeedback(BaseModel):
    Decision: DecisionBlock
    HardSkills: HardSkillsBlock
    SoftSkills: SoftSkillsBlock
    Roadmap: RoadmapBlock
    Summary: str

    @classmethod
    def model_validate(cls, data: Any) -> "FinalFeedback":
        if not isinstance(data, dict):
            raise ValidationError("FinalFeedback must be an object")
        required = ["Decision", "HardSkills", "SoftSkills", "Roadmap", "Summary"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"FinalFeedback missing fields: {', '.join(missing)}")
        decision = DecisionBlock.model_validate(data["Decision"])
        hard = HardSkillsBlock.model_validate(data["HardSkills"])
        soft = SoftSkillsBlock.model_validate(data["SoftSkills"])
        roadmap = RoadmapBlock.model_validate(data["Roadmap"])
        summary = data["Summary"]
        if not isinstance(summary, str):
            raise ValidationError("Summary must be a string")
        if hard.KnowledgeGaps and not roadmap.NextSteps:
            raise ValidationError("Roadmap.NextSteps must be non-empty when KnowledgeGaps exist")
        return cls(Decision=decision, HardSkills=hard, SoftSkills=soft, Roadmap=roadmap, Summary=summary)

    def model_dump(self) -> Dict[str, Any]:
        return {
            "Decision": self.Decision.model_dump(),
            "HardSkills": self.HardSkills.model_dump(),
            "SoftSkills": self.SoftSkills.model_dump(),
            "Roadmap": self.Roadmap.model_dump(),
            "Summary": self.Summary,
        }

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)


class StopIntentOutput(BaseModel):
    stop: bool
    confidence: int
    rationale: str

    @classmethod
    def model_validate(cls, data: Any) -> "StopIntentOutput":
        if not isinstance(data, dict):
            raise ValidationError("StopIntentOutput must be an object")
        required = ["stop", "confidence", "rationale"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"StopIntentOutput missing fields: {', '.join(missing)}")
        stop = data["stop"]
        confidence = data["confidence"]
        rationale = data["rationale"]
        if not isinstance(stop, bool):
            raise ValidationError("stop must be a boolean")
        if not isinstance(confidence, int) or confidence < 0 or confidence > 100:
            raise ValidationError("confidence must be 0..100")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 200:
            raise ValidationError("rationale must be 1..200 chars")
        return cls(stop=stop, confidence=confidence, rationale=rationale)

    def model_dump(self) -> Dict[str, Any]:
        return {
            "stop": self.stop,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


class CandidateProfileOutput(BaseModel):
    name: str
    level: str
    position: str
    skills: list
    confidence: dict
    assumptions: list

    @classmethod
    def model_validate(cls, data: Any) -> "CandidateProfileOutput":
        if not isinstance(data, dict):
            raise ValidationError("CandidateProfileOutput must be an object")
        required = ["name", "level", "position", "skills"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValidationError(f"CandidateProfileOutput missing fields: {', '.join(missing)}")
        name = data.get("name") or ""
        level = data.get("level") or "Unknown"
        position = data.get("position") or ""
        skills = data.get("skills") or []
        if not isinstance(name, str):
            raise ValidationError("name must be a string")
        if not isinstance(level, str):
            raise ValidationError("level must be a string")
        if not isinstance(position, str):
            raise ValidationError("position must be a string")
        if not isinstance(skills, list):
            raise ValidationError("skills must be a list")
        confidence = data.get("confidence") or {}
        assumptions = data.get("assumptions") or []
        if not isinstance(confidence, dict):
            raise ValidationError("confidence must be an object")
        if not isinstance(assumptions, list):
            raise ValidationError("assumptions must be a list")
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
            "confidence": dict(self.confidence),
            "assumptions": list(self.assumptions),
        }
