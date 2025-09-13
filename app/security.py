from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_sync_session
from .models import APIToken, User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def mask_token(token: str) -> str:
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token(user_id: int, db: Session) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    db.add(APIToken(user_id=user_id, token_hash=token_hash))
    db.flush()
    return token


def get_current_user(
    cred: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
):
    if cred is None or cred.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = cred.credentials
    token_hash = hash_token(token)
    with get_sync_session() as db:
        token_row = db.execute(select(APIToken).where(APIToken.token_hash == token_hash)).scalar_one_or_none()
        if not token_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        token_row.last_used_at = datetime.utcnow()
        user = db.get(User, token_row.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
        return user

