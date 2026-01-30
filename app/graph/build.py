"""Build the LangGraph StateGraph for the interview loop."""
from __future__ import annotations

from app.graph.nodes import (
    intake_node,
    profile_extract_node,
    stop_intent_node,
    observer_evaluate_node,
    robustness_detect_node,
    policy_update_node,
    factcheck_node,
    answer_candidate_node,
    refocus_node,
    hallucination_node,
    interviewer_generate_node,
    logger_node,
    final_feedback_node,
    final_logger_node,
)


def build_graph():
    try:
        from langgraph.graph import StateGraph, END
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "LangGraph is required to build the interview graph. Install 'langgraph'."
        ) from exc

    def _wrap(node_fn):
        def _inner(state):
            updates = node_fn(state)
            if updates is None:
                return state
            if isinstance(updates, dict):
                merged = dict(state)
                merged.update(updates)
                return merged
            return state

        return _inner

    graph = StateGraph(dict)

    graph.add_node("intake", _wrap(intake_node))
    graph.add_node("profile_extract", _wrap(profile_extract_node))
    graph.add_node("stop_intent", _wrap(stop_intent_node))
    graph.add_node("observer_evaluate", _wrap(observer_evaluate_node))
    graph.add_node("robustness_detect", _wrap(robustness_detect_node))
    graph.add_node("policy_update", _wrap(policy_update_node))
    graph.add_node("factcheck", _wrap(factcheck_node))
    graph.add_node("answer_candidate", _wrap(answer_candidate_node))
    graph.add_node("refocus", _wrap(refocus_node))
    graph.add_node("hallucination", _wrap(hallucination_node))
    graph.add_node("interviewer_generate", _wrap(interviewer_generate_node))
    graph.add_node("logger", _wrap(logger_node))
    graph.add_node("final_feedback", _wrap(final_feedback_node))
    graph.add_node("final_logger", _wrap(final_logger_node))

    graph.set_entry_point("intake")

    graph.add_edge("intake", "profile_extract")
    graph.add_edge("profile_extract", "stop_intent")

    def route_after_stop_detector(state):
        return "final" if state.get("stop_requested") else "continue"

    graph.add_conditional_edges(
        "stop_intent",
        route_after_stop_detector,
        {
            "final": "final_feedback",
            "continue": "observer_evaluate",
        },
    )

    graph.add_edge("final_feedback", "final_logger")
    graph.add_edge("final_logger", END)

    graph.add_edge("observer_evaluate", "robustness_detect")
    graph.add_edge("robustness_detect", "policy_update")

    def route_after_policy(state):
        route = state.get("route", "normal")
        if route == "answer_candidate":
            return "answer_candidate"
        if route == "refocus":
            return "refocus"
        if route == "hallucination":
            return "hallucination"
        return "normal"

    graph.add_conditional_edges(
        "policy_update",
        route_after_policy,
        {
            "answer_candidate": "answer_candidate",
            "refocus": "refocus",
            "hallucination": "factcheck",
            "normal": "interviewer_generate",
        },
    )

    graph.add_edge("factcheck", "hallucination")
    graph.add_edge("answer_candidate", "interviewer_generate")
    graph.add_edge("refocus", "interviewer_generate")
    graph.add_edge("hallucination", "interviewer_generate")

    graph.add_edge("interviewer_generate", "logger")
    graph.add_edge("logger", END)

    return graph.compile()
