from __future__ import annotations

from typing import Any, Dict, List

import httpx
from langgraph.graph import END, START, StateGraph

from app.config import get_settings
from .openai_client import chat


class AgentState(dict):
    pass


async def intent_classifier(state: AgentState) -> str:
    text = state["input"]
    prompt = [
        {"role": "system", "content": "Classify intent: task_create, task_query, plan, schedule, other."},
        {"role": "user", "content": text},
    ]
    out = chat(prompt).strip().lower()
    for k in ["task_create", "task_query", "plan", "schedule"]:
        if k in out:
            state["intent"] = k
            return k
    state["intent"] = "task_create"
    return "task_create"


async def parser_node(state: AgentState) -> AgentState:
    # simple passthrough; API will parse
    return state


async def task_crud_node(state: AgentState) -> AgentState:
    s = get_settings()
    token = state["token"]
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"http://{s.app_host}:{s.app_port}/mcp/nl_to_task",
            headers={"Authorization": f"Bearer {token}"},
            json={"text": state["input"]},
            timeout=20,
        )
        r.raise_for_status()
        state["result"] = r.json()
    return state


async def planner_node(state: AgentState) -> AgentState:
    s = get_settings()
    token = state["token"]
    horizon = "week" if "week" in state["input"].lower() else "day"
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"http://{s.app_host}:{s.app_port}/planning/plan",
            headers={"Authorization": f"Bearer {token}"},
            json={"horizon": horizon},
            timeout=20,
        )
        r.raise_for_status()
        state["result"] = r.json()
    return state


async def scheduler_node(state: AgentState) -> AgentState:
    # naive: no-op here; scheduling driven via /tasks and reminders endpoints
    return state


async def notifier_node(state: AgentState) -> AgentState:
    return state


async def guardrail_node(state: AgentState) -> AgentState:
    # ensure we never leak tokens
    if "token" in state:
        state["token"] = "***"
    return state


async def finalizer_node(state: AgentState) -> AgentState:
    intent = state.get("intent")
    if intent == "task_create":
        task = state.get("result", {})
        state["output"] = f"Created task: {task.get('title')} (id={task.get('id')})"
    elif intent == "plan":
        plan = state.get("result", {})
        state["output"] = plan.get("summary", "Plan ready.")
    else:
        state["output"] = "Done."
    return state


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("intent", intent_classifier)
    g.add_node("parser", parser_node)
    g.add_node("task_crud", task_crud_node)
    g.add_node("planner", planner_node)
    g.add_node("scheduler", scheduler_node)
    g.add_node("notifier", notifier_node)
    g.add_node("guardrail", guardrail_node)
    g.add_node("final", finalizer_node)

    g.add_edge(START, "intent")
    g.add_conditional_edges(
        "intent",
        lambda s: s.get("intent"),
        {"task_create": "task_crud", "plan": "planner", "task_query": "planner", "schedule": "scheduler"},
    )
    g.add_edge("task_crud", "guardrail")
    g.add_edge("planner", "guardrail")
    g.add_edge("scheduler", "guardrail")
    g.add_edge("guardrail", "final")
    g.add_edge("final", END)
    return g.compile()

