from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import Task
from ..schemas import ExportOut, ImportPayload, TaskOut
from ..security import get_current_user

router = APIRouter(prefix="/io", tags=["import_export"])


@router.post("/import", response_model=dict)
async def import_tasks(body: ImportPayload, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    created = 0
    for it in body.tasks:
        t = Task(
            user_id=user.id,
            title=it.title,
            notes=it.notes,
            due=it.due,
            priority=it.priority,
            recurrence=it.recurrence,
        )
        session.add(t)
        created += 1
    await session.flush()
    return {"created": created}


@router.get("/export", response_model=ExportOut)
async def export_tasks(user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(Task).where(Task.user_id == user.id))
    tasks = [TaskOut.model_validate(t) for t in res.scalars().all()]
    return ExportOut(tasks=tasks)

