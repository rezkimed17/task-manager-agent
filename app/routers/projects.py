from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import Project
from ..schemas import ProjectIn, ProjectOut
from ..security import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectOut])
async def list_projects(user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(Project).where(Project.user_id == user.id).order_by(Project.name))
    return [ProjectOut.model_validate(p) for p in res.scalars().all()]


@router.post("/", response_model=ProjectOut)
async def create_project(body: ProjectIn, user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    exists = await session.execute(select(Project).where(and_(Project.user_id == user.id, Project.name == body.name)))
    if exists.scalars().first():
        raise HTTPException(status_code=409, detail="Project exists")
    p = Project(user_id=user.id, name=body.name)
    session.add(p)
    await session.flush()
    return ProjectOut.model_validate(p)

