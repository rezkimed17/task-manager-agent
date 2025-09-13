from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import Task
from ..planner import plan_day, plan_week
from ..schemas import PlanOut, PlanRequest
from ..security import get_current_user

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/plan", response_model=PlanOut)
async def plan(body: PlanRequest, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(Task).where(Task.user_id == user.id))
    tasks = [
        {
            "id": t.id,
            "title": t.title,
            "due": t.due,
            "priority": t.priority,
            "completed": t.completed,
        }
        for t in res.scalars().all()
    ]
    if body.horizon == "week":
        return PlanOut(**plan_week(tasks))
    return PlanOut(**plan_day(tasks))

