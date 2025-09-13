from __future__ import annotations

import re
from app.parser import parse_natural_language


def test_parse_basic():
    parsed = parse_natural_language("Email Sara tomorrow at 9 #work !high in [Sales]")
    assert parsed["title"].lower().startswith("email sara")
    assert "work" in parsed["tags"]
    assert parsed["priority"] == 1
    assert parsed["project"] == "Sales"
    assert parsed["due"] is not None


def test_recurrence_every_day():
    parsed = parse_natural_language("Write journal every day")
    assert parsed["recurrence"] == "RRULE:FREQ=DAILY"

