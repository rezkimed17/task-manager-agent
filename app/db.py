from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import AsyncIterator, Iterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


settings = get_settings()
async_engine = create_async_engine(settings.database_url, echo=False, future=True)
async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False, autoflush=False)

sync_engine = None
SyncSessionLocal: sessionmaker | None = None
if settings.sync_database_url:
    from sqlalchemy import create_engine

    sync_engine = create_engine(settings.sync_database_url, future=True)
    SyncSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=sync_engine,
    )


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:  # type: AsyncSession
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextmanager
def get_sync_session() -> Iterator[Session]:
    if SyncSessionLocal is None:
        raise RuntimeError("Sync session not configured")
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
