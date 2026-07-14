"""Open-Meteo günlük proqnoz (pulsuz, açarsız) — 16 günlük üfüq, heç vaxt raise etmir."""

import logging
from datetime import date, timedelta

import httpx

from .cache import MISS, KVCache

logger = logging.getLogger("voyagent.weather")

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HORIZON_DAYS = 15  # bugün + 15 = Open-Meteo-nun 16 günlük limiti

_cache = KVCache("weather")


async def get_daily(
    lat: float, lon: float, start_date: date, end_date: date
) -> list[dict | None]:
    """Trip-in hər günü üçün {"code","t_max","t_min","precip"} və ya None (üfüqdən kənar/xəta)."""
    num_days = (end_date - start_date).days + 1
    horizon = date.today() + timedelta(days=HORIZON_DAYS)
    if start_date > horizon:
        return [None] * num_days

    fetch_end = min(end_date, horizon)
    key = f"{round(lat, 2)}:{round(lon, 2)}:{start_date}:{fetch_end}:{date.today()}"
    cached = await _cache.get(key)
    if cached is MISS:
        cached = await _fetch(lat, lon, start_date, fetch_end)
        if cached is not None:
            await _cache.set(key, cached)

    if not cached:
        return [None] * num_days
    # Üfüqə görə kəsilmiş quyruq günləri None ilə doldurulur
    return cached + [None] * (num_days - len(cached))


async def _fetch(lat: float, lon: float, start: date, end: date) -> list[dict | None] | None:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "start_date": str(start),
        "end_date": str(end),
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(FORECAST_URL, params=params)
        data = resp.json().get("daily", {}) if resp.status_code == 200 else {}
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Hava proqnozu xətası: %s", e)
        return None

    codes = data.get("weather_code") or []
    if not codes:
        return None
    t_max = data.get("temperature_2m_max") or []
    t_min = data.get("temperature_2m_min") or []
    precip = data.get("precipitation_probability_max") or []

    def val(seq, i):
        return seq[i] if i < len(seq) and seq[i] is not None else None

    result: list[dict | None] = []
    for i in range(len(codes)):
        if codes[i] is None:
            result.append(None)
            continue
        result.append({
            "code": int(codes[i]),
            "t_max": round(val(t_max, i)) if val(t_max, i) is not None else None,
            "t_min": round(val(t_min, i)) if val(t_min, i) is not None else None,
            "precip": int(val(precip, i)) if val(precip, i) is not None else None,
        })
    return result
