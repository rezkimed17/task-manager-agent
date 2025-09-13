from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List


def prioritize(tasks: List[Dict[str, Any]], now: dt.datetime | None = None) -> List[Dict[str, Any]]:
    now = now or dt.datetime.now(dt.timezone.utc)
    def score(t: Dict[str, Any]) -> float:
        pr = t.get("priority", 3)
        due = t.get("due")
        overdue_bonus = 0.0
        if due is not None:
            if due.tzinfo is None:
                due = due.replace(tzinfo=dt.timezone.utc)
            delta = (due - now).total_seconds()
            # earlier due -> lower score
            due_score = max(-delta / 86400.0, -7.0)
            overdue_bonus = 5.0 if delta < 0 else 0.0
        else:
            due_score = 0.0
        base = 6 - pr
        return base + due_score + overdue_bonus
    return sorted(tasks, key=score, reverse=True)


def plan_day(tasks: List[Dict[str, Any]], max_items: int = 8) -> Dict[str, Any]:
    ordered = prioritize(tasks)
    return {
        "summary": "Day plan based on priority and due dates.",
        "items": [t for t in ordered if not t.get("completed")][:max_items],
    }


def plan_week(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = prioritize(tasks)
    buckets = {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": [], "Sat": [], "Sun": []}
    i = 0
    for t in ordered:
        if t.get("completed"):
            continue
        day = list(buckets.keys())[i % 7]
        buckets[day].append(t)
        i += 1
    items: List[Dict[str, Any]] = []
    for d, ts in buckets.items():
        items.append({"day": d, "tasks": ts[:5]})
    return {"summary": "Week plan proposal.", "items": items}

