"""Utilities for maintaining skill matrix state."""
from __future__ import annotations

from typing import Any, Dict, Iterable


def apply_skill_updates(skill_matrix: Dict[str, Any], updates: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    updated = dict(skill_matrix or {})

    for item in updates or []:
        topic = item.get("topic")
        status = item.get("status")
        evidence = item.get("evidence")
        if not topic:
            continue

        entry = updated.get(topic, {"status": None, "evidence": []})
        current_status = entry.get("status")
        evidence_list = list(entry.get("evidence", []))

        if evidence:
            evidence_list.append(evidence)

        # Allow upgrade from gap/uncertain to confirmed; preserve confirmed status.
        if current_status == "confirmed" and status != "confirmed":
            new_status = current_status
        else:
            new_status = status or current_status

        updated[topic] = {"status": new_status, "evidence": evidence_list}

    return updated

