"""Agentlərin ortaq LLM helper-ləri: JSON çıxarma və qısa mətn mesajları."""

import json

from ..llm.client import LLMResult, call_llm


class AgentError(Exception):
    pass


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise AgentError("Cavabda JSON tapılmadı")
    return json.loads(text[start : end + 1])


async def ask_json(system: str, user: str, max_tokens: int, temperature: float = 0.7) -> tuple[dict, LLMResult]:
    """JSON gözlənilən agent çağırışı; parse alınmasa 1 dəfə sərt təkrar sorğu."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    result = await call_llm(messages, max_tokens=max_tokens, temperature=temperature, json_mode=True)
    try:
        return _extract_json(result.content), result
    except (AgentError, json.JSONDecodeError):
        retry_messages = messages + [
            {"role": "assistant", "content": result.content},
            {"role": "user", "content": "Cavab düzgün JSON deyildi. YALNIZ düzgün JSON qaytar, başqa heç nə."},
        ]
        retry = await call_llm(retry_messages, max_tokens=max_tokens, temperature=0.3, json_mode=True)
        try:
            return _extract_json(retry.content), retry
        except (AgentError, json.JSONDecodeError) as e:
            raise AgentError(f"LLM düzgün JSON qaytarmadı: {e}")


async def ask_text(system: str, user: str, max_tokens: int = 120, temperature: float = 0.5) -> tuple[str, LLMResult]:
    """Qısa 'danışıq' mesajı üçün çağırış (token limiti kiçik saxlanılır)."""
    result = await call_llm(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=False,
    )
    return result.content.strip().strip('"'), result
