"""LangGraph nodes for the interview flow."""
from __future__ import annotations

from typing import Any, Dict

from app.logging.interview_logger import InterviewLogger
from app.state.schema import CandidateProfile
from app.agents.observer import run_observer
from app.agents.interviewer import run_interviewer
from app.agents.fact_checker import run_factchecker
from app.agents.hiring_manager import run_hiring_manager
from app.agents.stop_intent import run_stop_intent
from app.agents.profile_extractor import extract_candidate_profile_llm
from app.memory.skills import apply_skill_updates
from app.llm.schemas import ObserverOutput, InterviewerOutput
from app.policies.adaptability import apply_difficulty, decide_action_type
from app.policies.context_guard import enforce_no_repeat, normalize_topic
from app.policies.question_bank import pick_next_question, get_candidates
from app.policies.topic_manager import select_next_topic
from app.policies.robustness import detect_robustness
from app.policies.router import choose_route
from app.evaluation.feedback_inputs import build_feedback_input
from app.policies.safety_limits import normalize_text
from app.memory.controls import detect_loop, break_loop


def intake_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize required state fields and ensure candidate_profile exists."""
    if "candidate_profile" not in state or state["candidate_profile"] is None:
        raise ValueError("candidate_profile must be provided before intake")

    candidate = state["candidate_profile"]
    if isinstance(candidate, dict):
        candidate = CandidateProfile.model_validate(candidate)

    updates = {
        "candidate_profile": candidate,
        "asked_questions": state.get("asked_questions", []),
        "history": state.get("history", []),
        "difficulty": state.get("difficulty", 1),
        "stop_requested": state.get("stop_requested", False),
        "skill_matrix": state.get("skill_matrix", {}),
    }
    return updates


def stop_detector_node(state: Dict[str, Any]) -> Dict[str, Any]:
    STOP_PHRASES = [
        "стоп интервью",
        "стоп игра",
        "давай фидбэк",
    ]
    user_message = (state.get("user_message") or "").lower()
    stop_requested = any(phrase in user_message for phrase in STOP_PHRASES)
    return {"stop_requested": stop_requested}


def stop_intent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    user_message = (state.get("user_message") or "").strip()
    if not user_message:
        return {"stop_requested": False, "stop_intent": {"stop": False, "confidence": 0, "rationale": "empty input"}}

    output = run_stop_intent(state)
    stop_by_intent = bool(output.stop and output.confidence >= 70)
    stop_by_phrases = bool(stop_detector_node(state).get("stop_requested"))
    stop_requested = stop_by_intent or stop_by_phrases

    internal_thoughts = state.get("internal_thoughts", "")
    line = f"[StopIntent]: stop={output.stop} confidence={output.confidence} reason=\"{output.rationale}\""
    internal_thoughts = f"{internal_thoughts}\n{line}" if internal_thoughts else line

    return {
        "stop_requested": stop_requested,
        "stop_intent": output.model_dump(),
        "internal_thoughts": internal_thoughts,
    }


def profile_extract_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("profile_extracted"):
        return {}
    # Extract only on the very first user message (before any turns are logged).
    if state.get("turn_id", -1) != -1:
        return {}
    user_message = (state.get("user_message") or "").strip()
    if not user_message:
        return {}

    extracted = extract_candidate_profile_llm(user_message)
    state["candidate_profile"] = extracted
    state["profile_extracted"] = True

    logger = InterviewLogger(
        log_path=state["log_path"],
        candidate_profile=extracted,
    )
    logger.set_candidate_profile(extracted)

    return {
        "candidate_profile": extracted,
        "profile_extracted": True,
    }


def interviewer_generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    asked_questions = list(state.get("asked_questions", []))
    history = list(state.get("history", []))

    output: InterviewerOutput = run_interviewer(state)
    message = output.agent_visible_message
    metadata = output.metadata

    history.append({"role": "interviewer", "content": message})

    planned_question = state.get("planned_question") if isinstance(state.get("planned_question"), dict) else None
    question_id = planned_question.get("question_id") if planned_question else None
    if isinstance(question_id, str) and question_id not in asked_questions:
        asked_questions.append(question_id)
        last_question_id = question_id
    else:
        last_question_id = state.get("last_question_id")

    topic_state = dict(state.get("topic_state") or {})
    if isinstance(metadata.topic, str) and metadata.topic:
        topic_state["current_topic"] = metadata.topic

    return {
        "agent_visible_message": message,
        "history": history,
        "asked_questions": asked_questions,
        "topic_state": topic_state,
        "interviewer_metadata": metadata.model_dump(),
        "last_question_id": last_question_id,
    }


def _format_internal_thoughts(observer_output: ObserverOutput) -> str:
    flags = observer_output.robustness.model_dump()
    return (
        f"[Observer]: {observer_output.summary} difficulty {observer_output.difficulty_delta:+d}.\n"
        f"[Observer→Interviewer]: {observer_output.next_action.instruction_to_interviewer}\n"
        f"[Robustness]: hallucination_claim={flags.get('hallucination_claim')}, "
        f"off_topic={flags.get('off_topic')}, role_reversal={flags.get('role_reversal')}, "
        f"evasive={flags.get('evasive')}"
    )


def observer_evaluate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    history = list(state.get("history", []))
    user_message = state.get("user_message", "")
    if user_message:
        history.append({"role": "candidate", "content": user_message})

    observer_output = run_observer({**state, "history": history})
    observer_json = observer_output.model_dump()

    skill_matrix = apply_skill_updates(
        state.get("skill_matrix", {}),
        observer_json.get("skill_updates", []),
    )

    internal_thoughts = _format_internal_thoughts(observer_output)

    return {
        "observer_json": observer_json,
        "risk_flags": observer_json.get("robustness", {}),
        "skill_matrix": skill_matrix,
        "internal_thoughts": internal_thoughts,
        "history": history,
    }


def robustness_detect_node(state: Dict[str, Any]) -> Dict[str, Any]:
    det = detect_robustness(state)
    route = choose_route(bool(state.get("stop_requested")), det)
    det_dict = {
        "off_topic": det.off_topic,
        "role_reversal": det.role_reversal,
        "hallucination_claim": det.hallucination_claim,
        "evasive": det.evasive,
        "reason": det.reason,
        "candidate_question": det.candidate_question,
        "suspicious_claim": det.suspicious_claim,
    }

    internal_thoughts = state.get("internal_thoughts", "")
    line = f"[RobustnessDetector]: route={route} reason={det.reason}"
    internal_thoughts = f"{internal_thoughts}\n{line}" if internal_thoughts else line

    return {
        "robustness_det": det_dict,
        "route": route,
        "internal_thoughts": internal_thoughts,
    }


def factcheck_node(state: Dict[str, Any]) -> Dict[str, Any]:
    det = state.get("robustness_det", {}) if isinstance(state.get("robustness_det"), dict) else {}
    claim = det.get("suspicious_claim")
    if not claim and isinstance(state.get("observer_json"), dict):
        detected = state.get("observer_json", {}).get("detected_claims", [])
        if isinstance(detected, list) and detected:
            first = detected[0]
            if isinstance(first, dict):
                claim = first.get("claim")
    if not claim:
        claim = state.get("user_message", "")

    verdict = run_factchecker(state, claim or "")

    factcheck_json = verdict.model_dump()
    internal_thoughts = state.get("internal_thoughts", "")
    line = (
        f"[FactChecker]: label={factcheck_json.get('label')} "
        f"confidence={factcheck_json.get('confidence')} "
        f"correction={factcheck_json.get('correction')}"
    )
    internal_thoughts = f"{internal_thoughts}\n{line}" if internal_thoughts else line

    return {
        "factcheck_json": factcheck_json,
        "internal_thoughts": internal_thoughts,
    }


def policy_update_node(state: Dict[str, Any]) -> Dict[str, Any]:
    observer_json = state.get("observer_json", {}) if isinstance(state.get("observer_json"), dict) else {}
    prev_action = state.get("action_type")

    route = state.get("route") or "normal"
    if route in {"answer_candidate", "refocus", "hallucination"}:
        action_type = route
    else:
        action_type = decide_action_type(observer_json, prev_action_type=prev_action)
    difficulty = apply_difficulty(state.get("difficulty", 1), observer_json.get("difficulty_delta", 0))

    topic_state = dict(state.get("topic_state") or {})
    last_topics = topic_state.get("last_topics", []) if isinstance(topic_state.get("last_topics", []), list) else []

    soft_topic = None
    if isinstance(observer_json.get("next_action"), dict):
        soft_topic = observer_json.get("next_action", {}).get("topic")
    soft_topic = normalize_topic(soft_topic) if soft_topic else None

    skill_matrix = state.get("skill_matrix", {})
    selected_topic = select_next_topic(skill_matrix, topic_state)
    if soft_topic and soft_topic not in last_topics[-2:]:
        selected_topic = soft_topic

    asked_questions = set(state.get("asked_questions", []))
    if action_type in {"answer_candidate", "refocus", "hallucination"}:
        followup_type = "ask"
    else:
        followup_type = action_type if action_type in {"ask", "clarify", "simplify", "hint"} else "ask"
    planned_question = pick_next_question(asked_questions, selected_topic, difficulty, followup_type)
    if planned_question is None:
        fallback_pool = get_candidates(None, difficulty, followup_type) or get_candidates(None, difficulty, None)
        planned_question = enforce_no_repeat(None, asked_questions, fallback_pool)
    if planned_question is None:
        for level in range(1, 6):
            fallback_pool = get_candidates(None, level, None)
            planned_question = enforce_no_repeat(None, asked_questions, fallback_pool)
            if planned_question is not None:
                break

    if planned_question and isinstance(planned_question.get("prompt"), str):
        if detect_loop(topic_state, planned_question.get("prompt")):
            selected_topic = break_loop(skill_matrix, topic_state)
            planned_question = pick_next_question(asked_questions, selected_topic, difficulty, followup_type)

    if selected_topic:
        last_topics.append(selected_topic)
        topic_state["current_topic"] = selected_topic
        topic_state["last_topics"] = last_topics[-5:]
        coverage = dict(topic_state.get("coverage") or {})
        coverage[selected_topic] = int(coverage.get(selected_topic, 0)) + 1
        topic_state["coverage"] = coverage

    return {
        "difficulty": difficulty,
        "action_type": action_type,
        "planned_question": planned_question,
        "topic_state": topic_state,
        "planned_response": None,
    }


def answer_candidate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    det = state.get("robustness_det", {}) if isinstance(state.get("robustness_det"), dict) else {}
    planned_response = {
        "type": "answer_candidate",
        "candidate_question": det.get("candidate_question") or state.get("user_message", ""),
        "answer_guidance": "Ответь кратко на вопрос кандидата, затем верни к интервью и задай следующий вопрос.",
    }
    return {
        "action_type": "answer_candidate",
        "planned_response": planned_response,
    }


def refocus_node(state: Dict[str, Any]) -> Dict[str, Any]:
    planned_question = state.get("planned_question") if isinstance(state.get("planned_question"), dict) else {}
    topic_state = state.get("topic_state", {}) if isinstance(state.get("topic_state"), dict) else {}
    topic = topic_state.get("current_topic") or planned_question.get("topic") or "тему интервью"
    planned_response = {
        "type": "refocus",
        "message": f"Давай вернёмся к интервью: сейчас проверим {topic}.",
        "followup_question": planned_question.get("prompt"),
    }
    return {
        "action_type": "refocus",
        "planned_response": planned_response,
    }


def hallucination_node(state: Dict[str, Any]) -> Dict[str, Any]:
    det = state.get("robustness_det", {}) if isinstance(state.get("robustness_det"), dict) else {}
    planned_question = state.get("planned_question") if isinstance(state.get("planned_question"), dict) else {}
    suspicious = det.get("suspicious_claim") or state.get("user_message", "")
    factcheck_json = state.get("factcheck_json") if isinstance(state.get("factcheck_json"), dict) else {}
    safe_response = factcheck_json.get("safe_response") or "Похоже на недостоверную информацию."
    planned_response = {
        "type": "hallucination",
        "suspicious_claim": suspicious,
        "factcheck": factcheck_json,
        "message": safe_response,
        "followup_question": planned_question.get("prompt"),
    }
    return {
        "action_type": "hallucination",
        "planned_response": planned_response,
    }


def final_feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger = InterviewLogger(log_path=state["log_path"])
    log_data = logger.load()
    feedback_input = build_feedback_input(state, log_data)
    final_feedback = run_hiring_manager(feedback_input)
    return {"final_feedback": final_feedback.model_dump()}


def logger_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger = InterviewLogger(
        log_path=state["log_path"],
        candidate_profile=state.get("candidate_profile") if isinstance(state.get("candidate_profile"), dict) else {},
    )
    new_turn_id = int(state.get("turn_id", 0)) + 1

    log_agent_message = state.get("last_agent_message")
    if log_agent_message is None:
        log_agent_message = ""
    agent_msg = normalize_text(log_agent_message, max_len=2000)
    user_msg = normalize_text(state.get("user_message", ""), max_len=4000)
    internal = normalize_text(state.get("internal_thoughts", " "), max_len=4000) or " "
    logger.append_turn(
        turn_id=new_turn_id,
        agent_visible_message=agent_msg,
        user_message=user_msg,
        internal_thoughts=internal,
    )

    return {
        "turn_id": new_turn_id,
        "last_agent_message": state.get("agent_visible_message", ""),
    }


def final_logger_node(state: Dict[str, Any]) -> Dict[str, Any]:
    logger = InterviewLogger(log_path=state["log_path"])
    logger.set_final_feedback(state.get("final_feedback"))
    return {}
