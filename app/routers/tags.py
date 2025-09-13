from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import Tag
from ..schemas import TagOut
from ..security import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[TagOut])
async def list_tags(user=Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(Tag).where(Tag.user_id == user.id).order_by(Tag.name))
    return [TagOut.model_validate(t) for t in res.scalars().all()]

