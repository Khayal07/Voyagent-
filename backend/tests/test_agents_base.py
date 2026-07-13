"""Ortaq agent helper-ləri: JSON çıxarma və retry."""

import pytest

from app.agents import base
from app.agents.base import AgentError, _extract_json
from app.llm.client import LLMResult


def test_extract_json_plain():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_code_fence():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_surrounding_prose():
    assert _extract_json('Here you go: {"a": 1} hope it helps') == {"a": 1}


def test_extract_json_missing_raises():
    with pytest.raises(AgentError):
        _extract_json("no json here")


async def test_ask_json_retries_on_invalid(monkeypatch):
    calls = []

    async def fake_call_llm(messages, max_tokens, temperature, json_mode):
        calls.append(messages)
        content = "not json" if len(calls) == 1 else '{"ok": true}'
        return LLMResult(content=content, provider="test", model="test")

    monkeypatch.setattr(base, "call_llm", fake_call_llm)
    data, _ = await base.ask_json("sys", "user", max_tokens=100)
    assert data == {"ok": True}
    assert len(calls) == 2


async def test_ask_json_fails_after_retry(monkeypatch):
    async def fake_call_llm(messages, max_tokens, temperature, json_mode):
        return LLMResult(content="still not json", provider="test", model="test")

    monkeypatch.setattr(base, "call_llm", fake_call_llm)
    with pytest.raises(AgentError):
        await base.ask_json("sys", "user", max_tokens=100)
