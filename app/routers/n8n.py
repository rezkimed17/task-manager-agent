from __future__ import annotations

import hmac
from hashlib import sha256

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from ..config import get_settings

router = APIRouter(prefix="/n8n", tags=["n8n"])


@router.post("/callback")
async def n8n_callback(request: Request, x_n8n_signature: str = Header(alias="X-N8N-Signature")):
    body = await request.body()
    settings = get_settings()
    expected = hmac.new(settings.n8n_webhook_secret.encode(), body, sha256).hexdigest()
    if not hmac.compare_digest(expected, x_n8n_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    return {"ok": True}

