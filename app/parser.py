from __future__ import annotations

import datetime as dt
import re
from typing import Optional, Tuple

import dateparser


PRIORITY_WORDS = {
    "low": 5,
    "medium": 3,
    "high": 1,
    "urgent": 1,
}


def parse_natural_language(text: str, tz: str = "America/New_York") -> dict:
    original = text
    title = text
    notes: Optional[str] = None
    tags: list[str] = []
    project: Optional[str] = None
    priority = 3
    recurrence: Optional[str] = None
    due: Optional[dt.datetime] = None

    # tags: #tag
    for m in re.finditer(r"#(\w+)", text):
        tags.append(m.group(1).lower())
    text = re.sub(r"#\w+", "", text)

    # project: in [Project]
    pm = re.search(r"\bin\s*\[(.+?)\]", text, flags=re.IGNORECASE)
    if pm:
        project = pm.group(1).strip()
        text = text.replace(pm.group(0), "")

    # priority: !high !low etc
    pr = re.search(r"!(high|medium|low|urgent)", text, flags=re.IGNORECASE)
    if pr:
        priority = PRIORITY_WORDS[pr.group(1).lower()]
        text = text.replace(pr.group(0), "")

    # recurrence: every day/week/month or cronish words
    rec = re.search(r"\bevery\s+(day|weekday|week|month|year)(?:\s+on\s+(mon|tue|wed|thu|fri|sat|sun))?", text, flags=re.IGNORECASE)
    if rec:
        unit = rec.group(1).lower()
        dow = rec.group(2).lower() if rec.group(2) else None
        if unit == "day":
            recurrence = "RRULE:FREQ=DAILY"
        elif unit == "weekday":
            recurrence = "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"
        elif unit == "week" and dow:
            days = {"mon":"MO","tue":"TU","wed":"WE","thu":"TH","fri":"FR","sat":"SA","sun":"SU"}
            recurrence = f"RRULE:FREQ=WEEKLY;BYDAY={days[dow]}"
        else:
            recurrence = f"RRULE:FREQ={unit.upper()}LY"
        text = text.replace(rec.group(0), "")

    # due date/time phrases
    dm = re.search(r"\bby\s+(.+)$", text, flags=re.IGNORECASE)
    if dm:
        date_str = dm.group(1).strip()
        parsed = dateparser.parse(date_str, settings={"TIMEZONE": tz, "RETURN_AS_TIMEZONE_AWARE": True})
        if parsed:
            due = parsed
            text = text.replace(dm.group(0), "")

    # reminders: "remind me to ... tomorrow at 9"
    if text.lower().startswith("remind me to "):
        text = text[len("remind me to ") :]

    title = text.strip(",. ")
    return {
        "title": title or original,
        "notes": notes,
        "tags": tags,
        "project": project,
        "priority": priority,
        "recurrence": recurrence,
        "due": due,
    }

