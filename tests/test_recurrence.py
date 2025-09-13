from __future__ import annotations

from app.parser import parse_natural_language


def test_weekday_rule():
    p = parse_natural_language("Standup every weekday")
    assert p["recurrence"] == "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"

def test_week_on_day():
    p = parse_natural_language("Team sync every week on Mon")
    assert p["recurrence"] == "RRULE:FREQ=WEEKLY;BYDAY=MO"

