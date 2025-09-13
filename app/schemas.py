from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    token: str


class ProjectIn(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TagIn(BaseModel):
    name: str


class TagOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TaskIn(BaseModel):
    title: str
    notes: Optional[str] = None
    due: Optional[dt.datetime] = None
    project_id: Optional[int] = None
    priority: int = Field(default=3, ge=1, le=5)
    recurrence: Optional[str] = None
    tags: list[str] = []


class TaskOut(BaseModel):
    id: int
    title: str
    notes: Optional[str] = None
    due: Optional[dt.datetime] = None
    project: Optional[ProjectOut] = None
    priority: int
    recurrence: Optional[str] = None
    completed: bool
    tags: list[TagOut] = []

    class Config:
        from_attributes = True


class ReminderIn(BaseModel):
    task_id: int
    remind_at: dt.datetime


class ReminderOut(BaseModel):
    id: int
    task_id: int
    remind_at: dt.datetime
    sent: bool

    class Config:
        from_attributes = True


class NLTaskRequest(BaseModel):
    text: str


class PlanRequest(BaseModel):
    horizon: str = Field(description="day or week", default="day")


class PlanOut(BaseModel):
    summary: str
    items: list[dict]


class ImportPayload(BaseModel):
    tasks: list[TaskIn]


class ExportOut(BaseModel):
    tasks: list[TaskOut]

