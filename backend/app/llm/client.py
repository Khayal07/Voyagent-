"""Mərkəzi LLM client: əsas provider OpenAI, xəta olduqda avtomatik OpenRouter fallback."""

import logging
from dataclasses import dataclass

import httpx

from ..config import settings

logger = logging.getLogger("voyagent.llm")

PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key": lambda: settings.openai_api_key,
        "model": lambda: settings.openai_model,
        "supports_json_mode": True,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": lambda: settings.openrouter_api_key,
        "model": lambda: settings.openrouter_model,
        "supports_json_mode": False,
    },
}


class LLMError(Exception):
    pass


@dataclass
class LLMResult:
    content: str
    provider: str
    model: str
    fallback_reason: str | None = None


async def _call_provider(
    provider: str, messages: list[dict], max_tokens: int, temperature: float, json_mode: bool
) -> LLMResult:
    cfg = PROVIDERS[provider]
    api_key = cfg["api_key"]()
    if not api_key or api_key.startswith("sk-..."):
        raise LLMError(f"{provider}: API açarı təyin edilməyib")

    payload: dict = {
        "model": cfg["model"](),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode and cfg["supports_json_mode"]:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            f"{cfg['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
    if resp.status_code != 200:
        raise LLMError(f"{provider}: HTTP {resp.status_code} — {resp.text[:200]}")

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"{provider}: gözlənilməz cavab formatı — {e}")
    if not content:
        raise LLMError(f"{provider}: boş cavab")
    return LLMResult(content=content, provider=provider, model=payload["model"])


async def call_llm(
    messages: list[dict],
    max_tokens: int = 800,
    temperature: float = 0.7,
    json_mode: bool = True,
) -> LLMResult:
    """Əsas provider ilə çağırır; uğursuz olarsa fallback-ə keçir və səbəbi qeyd edir."""
    primary = settings.primary_provider
    fallback = "openrouter" if primary == "openai" else "openai"

    try:
        result = await _call_provider(primary, messages, max_tokens, temperature, json_mode)
        logger.info("LLM cavabı: provider=%s model=%s", result.provider, result.model)
        return result
    except (LLMError, httpx.HTTPError) as e:
        reason = str(e)
        logger.warning("Primary provider '%s' uğursuz oldu: %s — fallback: %s", primary, reason, fallback)

    result = await _call_provider(fallback, messages, max_tokens, temperature, json_mode)
    result.fallback_reason = reason
    logger.info("LLM cavabı (fallback): provider=%s model=%s", result.provider, result.model)
    return result
