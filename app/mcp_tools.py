from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import async_session_factory, get_async_session
from .models import AuditLog, Project, Reminder, Tag, Task
from .parser import parse_natural_language
from .schemas import TaskIn, TaskOut
from .security import get_current_user

router = APIRouter(prefix="/mcp", tags=["mcp"])


async def record_audit(session: AsyncSession, user_id: int, action: str, payload: str, idem_key: str | None):
    al = AuditLog(user_id=user_id, action=action, payload=payload, idempotency_key=idem_key)
    session.add(al)


@router.post("/create_task", response_model=TaskOut)
async def create_task(
    req: Request,
    body: TaskIn,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    idempotency_key: Optional[str] = Header(default=None, convert_underscores=False, alias="Idempotency-Key"),
):
    settings = get_settings()
    if idempotency_key:
        res = await session.execute(
            select(AuditLog).where(
                and_(AuditLog.user_id == user.id, AuditLog.idempotency_key == idempotency_key, AuditLog.action == "create_task")
            )
        )
        if res.first():
            # find last task with same title for simplicity
            existing = await session.execute(
                select(Task).where(and_(Task.user_id == user.id, Task.title == body.title)).order_by(Task.id.desc())
            )
            task = existing.scalars().first()
            if task:
                return await _task_out(session, task)

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
    if body.tags:
        for tname in body.tags:
            tname = tname.lower()
            res = await session.execute(select(Tag).where(and_(Tag.user_id == user.id, Tag.name == tname)))
            tag = res.scalars().first()
            if not tag:
                tag = Tag(user_id=user.id, name=tname)
                session.add(tag)
            task.tags.append(tag)
    if settings.dry_run:
        raise HTTPException(status_code=409, detail="DRY_RUN enabled; task not created")
    await record_audit(session, user.id, "create_task", body.model_dump_json(), idempotency_key)
    await session.flush()
    return await _task_out(session, task)


async def _task_out(session: AsyncSession, task: Task) -> TaskOut:
    await session.refresh(task)
    return TaskOut.model_validate(task)


@router.post("/update_task/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, body: Dict[str, Any], user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    task = await session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    for k in ["title", "notes", "due", "priority", "recurrence", "completed"]:
        if k in body:
            setattr(task, k, body[k])
    if "tags" in body and isinstance(body["tags"], list):
        task.tags.clear()
        for tname in body["tags"]:
            res = await session.execute(select(Tag).where(and_(Tag.user_id == user.id, Tag.name == tname)))
            tag = res.scalars().first()
            if not tag:
                tag = Tag(user_id=user.id, name=tname)
                session.add(tag)
            task.tags.append(tag)
    await session.flush()
    return await _task_out(session, task)


@router.get("/list_tasks", response_model=list[TaskOut])
async def list_tasks(user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(Task).where(Task.user_id == user.id).order_by(Task.due.is_(None), Task.due))
    tasks = res.scalars().unique().all()
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/search_tasks", response_model=list[TaskOut])
async def search_tasks(q: str, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    # SQLite FTS5
    sql = """
      SELECT t.* FROM tasks t
      JOIN tasks_fts f ON t.id=f.rowid
      WHERE f MATCH :q AND t.user_id=:uid
    """
    rows = (await session.execute(sql, {"q": q, "uid": user.id})).mappings().all()
    tasks = [Task(**row) for row in rows]
    return [TaskOut.model_validate(t) for t in tasks]


@router.post("/schedule_reminder", response_model=dict)
async def schedule_reminder(body: Dict[str, Any], user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    task_id = body.get("task_id")
    remind_at = body.get("remind_at")
    if not task_id or not remind_at:
        raise HTTPException(status_code=400, detail="task_id and remind_at required")
    task = await session.get(Task, task_id)
    if not task or task.user_id != user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    if isinstance(remind_at, str):
        remind_at = dt.datetime.fromisoformat(remind_at)
    session.add(Reminder(user_id=user.id, task_id=task.id, remind_at=remind_at))
    await session.flush()
    return {"ok": True}


@router.post("/send_email_notification", response_model=dict)
async def send_email_notification_api(body: Dict[str, Any], user=Depends(get_current_user)):
    # The real send is done by scheduler via n8n webhook; this is a no-op placeholder for MCP interface
    title = body.get("title", "")
    reason = body.get("reason", "event")
    return {"queued": True, "title": title, "reason": reason}


@router.post("/import_tasks", response_model=dict)
async def import_tasks(body: Dict[str, Any], user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    items = body.get("tasks", [])
    created = 0
    for it in items:
        task = Task(
            user_id=user.id,
            title=it.get("title", "Untitled"),
            notes=it.get("notes"),
            due=dt.datetime.fromisoformat(it["due"]) if it.get("due") else None,
            priority=int(it.get("priority", 3)),
            recurrence=it.get("recurrence"),
        )
        session.add(task)
        created += 1
    await session.flush()
    return {"created": created}


@router.get("/export_tasks", response_model=dict)
async def export_tasks(user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(Task).where(Task.user_id == user.id))
    tasks = res.scalars().all()
    out = []
    for t in tasks:
        out.append(
            {
                "id": t.id,
                "title": t.title,
                "notes": t.notes,
                "due": t.due.isoformat() if t.due else None,
                "priority": t.priority,
                "recurrence": t.recurrence,
                "completed": t.completed,
                "tags": [tg.name for tg in t.tags],
            }
        )
    return {"tasks": out}


@router.post("/nl_to_task", response_model=TaskOut)
async def nl_to_task(body: Dict[str, Any], user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    parsed = parse_natural_language(text)
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
    return await _task_out(session, task)
