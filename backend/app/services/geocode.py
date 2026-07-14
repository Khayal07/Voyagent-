"""Nominatim (OpenStreetMap) geocoding — davamlı cache + 1 sorğu/saniyə rate limit."""

import asyncio
import logging
import time

import httpx

from .cache import MISS, KVCache

logger = logging.getLogger("voyagent.geocode")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "Voyagent/0.1 (educational project)"

_cache = KVCache("geo")
_lock = asyncio.Lock()
_last_request = 0.0


async def _search(key: str, params: dict) -> tuple[float, float] | None:
    global _last_request
    cached = await _cache.get(key)
    if cached is not MISS:
        return (cached[0], cached[1]) if cached else None

    async with _lock:
        # Nominatim istifadə şərtləri: maksimum 1 sorğu/saniyə
        wait = 1.0 - (time.monotonic() - _last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_request = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(NOMINATIM_URL, params=params, headers={"User-Agent": USER_AGENT})
            results = resp.json() if resp.status_code == 200 else []
        except httpx.HTTPError as e:
            logger.warning("Geocode xətası (%s): %s", key, e)
            results = []

    coords = (float(results[0]["lat"]), float(results[0]["lon"])) if results else None
    if coords is None:
        logger.info("Geocode tapılmadı: %s", key)
    await _cache.set(key, list(coords) if coords else None)
    return coords


async def geocode(name: str, city: str = "") -> tuple[float, float] | None:
    """Yerin (lat, lon) koordinatını qaytarır; tapılmasa None. Nəticələr cache-lənir."""
    q = f"{name}, {city}" if city else name
    return await _search(q.lower().strip(), {"q": q, "format": "json", "limit": 1})


async def geocode_near(name: str, center: tuple[float, float]) -> tuple[float, float] | None:
    """Adı şəhər mərkəzi ətrafındakı (~±0.3°) pəncərədə axtarır — 'ad, şəhər' alınmayanda fallback."""
    lat, lon = center
    key = f"{name}|near|{round(lat, 2)},{round(lon, 2)}".lower().strip()
    params = {
        "q": name,
        "format": "json",
        "limit": 1,
        "viewbox": f"{lon - 0.3},{lat + 0.3},{lon + 0.3},{lat - 0.3}",
        "bounded": 1,
    }
    return await _search(key, params)
