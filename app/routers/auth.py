from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_sync_session
from ..models import User
from ..schemas import LoginRequest, TokenOut
from ..security import issue_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest):
    with get_sync_session() as db:  # type: Session
        user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = issue_token(user.id, db)
        return TokenOut(token=token)

