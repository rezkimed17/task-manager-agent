from __future__ import annotations

import datetime as dt

from app.planner import plan_day, prioritize


def test_prioritize_overdue():
    now = dt.datetime.now(dt.timezone.utc)
    tasks = [
        {"title": "A", "priority": 3, "due": now - dt.timedelta(hours=1)},
        {"title": "B", "priority": 1, "due": now + dt.timedelta(days=1)},
    ]
    ordered = prioritize(tasks, now=now)
    assert ordered[0]["title"] == "A"


def test_plan_day_limits():
    tasks = [{"title": f"T{i}", "priority": 3} for i in range(20)]
    p = plan_day(tasks)
    assert len(p["items"]) <= 8

