from __future__ import annotations

import asyncio
import logging
import os

import orjson
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import get_settings
from .db import async_session_factory
from .logging import RequestIDMiddleware, configure_logging
from .metrics import REQUEST_COUNT, REQUEST_LATENCY
from .mcp_tools import router as mcp_router
from .routers import __init__ as _routers
from .routers.auth import router as auth_router
from .routers.health import router as health_router
from .routers.import_export import router as io_router
from .routers.n8n import router as n8n_router
from .routers.planning import router as planning_router
from .routers.projects import router as projects_router
from .routers.tasks import router as tasks_router
from .scheduler import scheduler_loop


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


app = FastAPI(title=settings.app_name, default_response_class=JSONResponse)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path
    with REQUEST_LATENCY.labels(method=method, path=path).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=method, path=path, code=str(response.status_code)).inc()
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(projects_router)
app.include_router(planning_router)
app.include_router(io_router)
app.include_router(n8n_router)
app.include_router(mcp_router)


stop_event = asyncio.Event()


@app.on_event("startup")
async def on_startup():
    # start scheduler
    app.state.scheduler_task = asyncio.create_task(scheduler_loop(async_session_factory, stop_event))
    logger.info("app started", extra={"request_id": "startup"})


@app.on_event("shutdown")
async def on_shutdown():
    stop_event.set()
    task = app.state.scheduler_task
    if task:
        await task
    logger.info("app stopped", extra={"request_id": "shutdown"})


@app.get("/")
def root():
    return {"name": settings.app_name, "env": settings.app_env}


# Static web UI
app.mount("/static", StaticFiles(directory="web", html=False), name="static")
@app.get("/web")
def web_index():
    with open("web/index.html", "r", encoding="utf-8") as f:
        return PlainTextResponse(f.read(), media_type="text/html")
