"""Valyuta məzənnələri — open.er-api.com (pulsuz, açarsız; attribution frontend footer-dədir)."""

import logging
from datetime import date

import httpx

from .cache import MISS, KVCache

logger = logging.getLogger("voyagent.rates")

RATES_URL = "https://open.er-api.com/v6/latest/{base}"
SUPPORTED = ("USD", "EUR", "AZN")

_cache = KVCache("rates")


async def get_rates(base: str) -> dict[str, float] | None:
    """Base valyutadan qalan SUPPORTED valyutalara məzənnələr; xətada None (cache yazılmır)."""
    base = base.upper()
    if base not in SUPPORTED:
        return None

    # Günlük açar — məzənnələr gündə bir dəfə yenilənir
    key = f"{base}:{date.today().isoformat()}"
    cached = await _cache.get(key)
    if cached is not MISS:
        return cached

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(RATES_URL.format(base=base))
        data = resp.json() if resp.status_code == 200 else {}
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Məzənnə xətası (%s): %s", base, e)
        return None

    if data.get("result") != "success":
        logger.warning("Məzənnə cavabı uğursuz (%s): %s", base, data.get("result"))
        return None

    all_rates = data.get("rates", {})
    rates = {cur: float(all_rates[cur]) for cur in SUPPORTED if cur != base and cur in all_rates}
    if not rates:
        return None

    await _cache.set(key, rates)
    return rates
