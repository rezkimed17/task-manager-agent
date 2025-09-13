from __future__ import annotations

import os
from typing import Any, Dict, List

from openai import OpenAI

from app.config import get_settings, get_llm_config


def get_openai() -> OpenAI:
    s = get_settings()
    os.environ.setdefault("OPENAI_API_KEY", s.openai_api_key)
    return OpenAI()


def chat(messages: List[Dict[str, str]]) -> str:
    s = get_settings()
    llm = get_llm_config()
    client = get_openai()
    resp = client.chat.completions.create(
        model=llm.model,
        temperature=llm.temperature,
        top_p=llm.top_p,
        messages=messages,
        max_tokens=llm.max_output_tokens,
    )
    return resp.choices[0].message.content or ""

