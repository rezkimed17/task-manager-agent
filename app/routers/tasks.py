from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import Project, Tag, Task
from ..parser import parse_natural_language
from ..schemas import NLTaskRequest, TaskIn, TaskOut
from ..security import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[TaskOut])
async def list_tasks(view: Optional[str] = Query(None), user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    q = select(Task).where(Task.user_id == user.id)
    now = dt.datetime.now(dt.timezone.utc)
    if view == "today":
        start = dt.datetime(now.year, now.month, now.day, tzinfo=dt.timezone.utc)
        end = start + dt.timedelta(days=1)
        q = q.where(and_(Task.due >= start, Task.due < end))
    elif view == "upcoming":
        q = q.where(Task.due >= now)
    elif view == "overdue":
        q = q.where(and_(Task.completed.is_(False), Task.due.is_not(None), Task.due < now))
    res = await session.execute(q.order_by(Task.due.is_(None), Task.due))
    tasks = res.scalars().unique().all()
    return [TaskOut.model_validate(t) for t in tasks]


@router.post("/", response_model=TaskOut)
async def create_task(body: TaskIn, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    project = None
    if body.project_id:
        project = await session.get(Project, body.project_id)
    task = Task(
        user_id=user.id,
        project_id=project.id if project else None,
        title=body.title,
        notes=body.notes,
        due=body.due,
        priority=body.priority,
        recurrence=body.recurrence,
    )
    session.add(task)
    for tname in body.tags:
        res = await session.execute(select(Tag).where(and_(Tag.user_id == user.id, Tag.name == tname)))
        tag = res.scalars().first()
        if not tag:
            tag = Tag(user_id=user.id, name=tname)
            session.add(tag)
        task.tags.append(tag)
    await session.flush()
    await session.refresh(task)
    return TaskOut.model_validate(task)


@router.post("/nl", response_model=TaskOut)
async def create_from_nl(body: NLTaskRequest, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    parsed = parse_natural_language(body.text)
    task = Task(
        user_id=user.id,
        title=parsed["title"],
        notes=parsed.get("notes"),
        due=parsed.get("due"),
        priority=parsed.get("priority", 3),
        recurrence=parsed.get("recurrence"),
    )
    session.add(task)
    for tname in parsed.get("tags", []) or []:
        res = await session.execute(select(Tag).where(and_(Tag.user_id == user.id, Tag.name == tname)))
        tag = res.scalars().first()
        if not tag:
            tag = Tag(user_id=user.id, name=tname)
            session.add(tag)
        task.tags.append(tag)
    await session.flush()
    await session.refresh(task)
    return TaskOut.model_validate(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, body: dict, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    task = await session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    for k in ["title", "notes", "due", "priority", "recurrence", "completed"]:
        if k in body:
            setattr(task, k, body[k])
    if "tags" in body:
        task.tags.clear()
        for tname in body["tags"]:
            res = await session.execute(select(Tag).where(and_(Tag.user_id == user.id, Tag.name == tname)))
            tag = res.scalars().first()
            if not tag:
                tag = Tag(user_id=user.id, name=tname)
                session.add(tag)
            task.tags.append(tag)
    await session.flush()
    await session.refresh(task)
    return TaskOut.model_validate(task)

