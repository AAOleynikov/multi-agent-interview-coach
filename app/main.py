from __future__ import annotations

import uuid

from app.graph.build import build_graph
from app.logging.interview_logger import InterviewLogger
from app.logging.paths import make_log_path
from app.state.schema import CandidateProfile, InterviewState

def main() -> None:
    greeting = (
        "Здравствуйте! Расскажите, пожалуйста, как вас зовут, ваш уровень, позицию и ключевые навыки.\n"
    )
    print(greeting)

    session_id = uuid.uuid4().hex
    log_path = make_log_path(session_id)

    candidate_profile = CandidateProfile(
        name=None,
        level="Unknown",
        position="",
        skills=[],
        confidence={},
        assumptions=[],
    )

    state = InterviewState(
        session_id=session_id,
        # Стартуем с -1, чтобы первый ход после ввода кандидата записался как turn_id=0
        turn_id=-1,
        candidate_profile=candidate_profile,
        history=[],
        log_path=log_path,
    ).model_dump()

    state.update(
        {
            "user_message": "",
            "agent_visible_message": "",
            "internal_thoughts": "",
            "asked_questions": [],
            "difficulty": 1,
            "stop_requested": False,
            "final_feedback": None,
            "observer_json": {},
            "risk_flags": {},
            "skill_matrix": {},
            "topic_state": {"current_topic": None, "last_topics": [], "coverage": {}},
            "interviewer_metadata": {},
            "planned_question": None,
            "planned_response": None,
            "action_type": None,
            "last_question_id": None,
            "robustness_det": {},
            "route": "normal",
            "factcheck_json": {},
            "last_user_message": None,
            "stop_intent": {},
            "profile_extracted": False,
            "last_agent_message": None,
        }
    )

    logger = InterviewLogger(
        log_path=log_path,
        candidate_profile=candidate_profile.model_dump(),
    )
    logger.init_log()
    # Запомним приветствие для первого хода; логгер запишет turn_id=0 после ответа пользователя.
    state["last_agent_message"] = greeting

    graph = build_graph()

    from app.policies.safety_limits import normalize_text

    # Первый ввод кандидата обязателен: он должен содержать данные для профиля.
    while True:
        first_input = input("Кандидат: ").strip()
        first_input_norm = normalize_text(first_input, max_len=4000)
        if first_input_norm:
            state["user_message"] = first_input_norm
            break
        print("Ответ не может быть пустым. Пожалуйста, представьтесь и укажите уровень/позицию/навыки.")

    try:
        state = graph.invoke(state)
    except Exception as exc:
        from app.logging.errors import log_error
        log_error(state.get("session_id", "unknown"), "graph.invoke", exc)
        raise
    state["last_user_message"] = state.get("user_message")

    while True:
        print(f"\nИнтервьюер: {state.get('agent_visible_message', '')}")

        # На каждом ходе требуем непустой ответ.
        while True:
            user_input = input("Кандидат: ").strip()
            user_message = normalize_text(user_input, max_len=4000)
            if user_message:
                state["user_message"] = user_message
                break
            print("Ответ не может быть пустым. Попробуйте ещё раз.")

        try:
            state = graph.invoke(state)
        except Exception as exc:
            from app.logging.errors import log_error
            log_error(state.get("session_id", "unknown"), "graph.invoke", exc)
            raise
        state["last_user_message"] = state.get("user_message")

        if state.get("stop_requested") and state.get("final_feedback") is not None:
            print("\nФинальный фидбэк:")
            try:
                from app.evaluation.render_feedback import render_final_feedback
                print(render_final_feedback(state["final_feedback"]))
            except Exception:
                print(state["final_feedback"])
            break


if __name__ == "__main__":
    main()
