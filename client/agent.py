from __future__ import annotations

import asyncio
import sys
from typing import Any

import httpx

from app.config import get_settings
from .graph import build_graph


async def run_agent_loop(token: str) -> None:
    app = build_graph()
    print("Task Manager Agent ready. Type 'exit' to quit.")
    while True:
        try:
            text = input("> ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text.lower() in {"exit", "quit"}:
            break
        state = {"input": text, "token": token}
        out = await app.ainvoke(state)  # type: ignore[attr-defined]
        print(out.get("output"))


async def login_and_get_token(email: str, password: str) -> str:
    s = get_settings()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"http://{s.app_host}:{s.app_port}/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        return r.json()["token"]


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m client.agent <email> <password>")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]
    token = asyncio.run(login_and_get_token(email, password))
    asyncio.run(run_agent_loop(token))


if __name__ == "__main__":
    main()

