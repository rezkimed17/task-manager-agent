from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UserMemory:
    timezone: str = "America/New_York"
    work_hours_start: str = "09:00"
    work_hours_end: str = "17:00"
    tag_rules: dict[str, str] = field(default_factory=dict)


memory = UserMemory()

