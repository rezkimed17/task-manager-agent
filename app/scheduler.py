from __future__ import annotations

import asyncio
import datetime as dt
import hmac
import json
import logging
from hashlib import sha256
from typing import Optional

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .models import Reminder, Task

logger = logging.getLogger(__name__)


async def send_email_notification(task_title: str, reason: str) -> None:
    settings = get_settings()
    url = settings.n8n_webhook_url
    payload = {"title": task_title, "reason": reason}
    body = json.dumps(payload).encode()
    sig = hmac.new(settings.n8n_webhook_secret.encode(), body, sha256).hexdigest()
    headers = {"X-N8N-Signature": sig, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, content=body, headers=headers)
        except Exception as e:
            logger.warning("n8n webhook failed: %s", str(e))


async def scheduler_loop(session_factory, stop_event: asyncio.Event):
    """Simple in-process scheduler checking reminders and overdue tasks.

    session_factory: async_sessionmaker
    """
    settings = get_settings()
    interval = 60
    while not stop_event.is_set():
        try:
            async with session_factory() as session:  # type: AsyncSession
                now = dt.datetime.now(dt.timezone.utc)
                # reminders due
                q = select(Reminder).where(and_(Reminder.sent.is_(False), Reminder.remind_at <= now))
                res = await session.execute(q)
                reminders = res.scalars().all()
                for r in reminders:
                    task = await session.get(Task, r.task_id)
                    if task:
                        await send_email_notification(task.title, "reminder")
                    r.sent = True
                # overdue notifications
                q2 = select(Task).where(
                    and_(Task.completed.is_(False), Task.due.is_not(None), Task.due < now)
                )
                res2 = await session.execute(q2)
                tasks = res2.scalars().all()
                for t in tasks:
                    await send_email_notification(t.title, "overdue")
                await session.commit()
        except Exception as e:
            logger.error("scheduler error: %s", str(e), extra={"request_id": "scheduler"})
        await asyncio.wait_for(stop_event.wait(), timeout=interval)

