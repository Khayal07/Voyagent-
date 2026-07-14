"""Geoapify Places — şəhər ətrafında real POI namizədləri (in-memory cache, pulsuz tier)."""

import logging
import math

import httpx

from ..config import settings

logger = logging.getLogger("voyagent.poi")

GEOAPIFY_URL = "https://api.geoapify.com/v2/places"
RADIUS_M = 7000
PER_CATEGORY = 8
MAX_NAME_LEN = 60
# Böyük hovuzdan məşhurluğa görə seçirik: OSM name:* tərcümə sayı + wiki tagı
POOL_LIMIT = 200
MIN_SPACING_M = 250

# Voyagent maraq kateqoriyaları → Geoapify kateqoriya id-ləri
CATEGORY_MAP = {
    "history": "tourism.sights,tourism.attraction,heritage",
    "nature": "natural,leisure.park",
    "food": "catering.restaurant,catering.cafe",
    "nightlife": "catering.bar,catering.pub,adult.nightclub",
    "art": "entertainment.museum,entertainment.culture",
    "shopping": "commercial.shopping_mall,commercial.marketplace",
}
DEFAULT_CATEGORIES = ["history", "nature", "food", "art"]

_cache: dict[tuple[float, float, str], list[dict]] = {}


def _fame(props: dict) -> int:
    """Məşhurluq balı: OSM name:* tərcümə sayı + wikipedia/wikidata tagı."""
    raw = (props.get("datasource") or {}).get("raw") or {}
    langs = sum(1 for k in raw if k.startswith("name:"))
    has_wiki = (
        "details.wiki_and_media" in (props.get("details") or [])
        or raw.get("wikipedia")
        or raw.get("wikidata")
    )
    return langs + (2 if has_wiki else 0)


def _dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(
        (a[0] - b[0]) * 111320,
        (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])),
    )


def _select(features: list[dict]) -> list[dict]:
    """Məşhurluğa görə sırala, yaxın dublikatları (məs. Forum mikro-abidələri) at."""
    ranked = sorted(features, key=lambda f: _fame(f.get("properties", {})), reverse=True)
    pois: list[dict] = []
    seen: set[str] = set()
    for f in ranked:
        props = f.get("properties", {})
        name = str(props.get("name", "")).strip()[:MAX_NAME_LEN]
        if not name or name.casefold() in seen or props.get("lat") is None or props.get("lon") is None:
            continue
        pt = (float(props["lat"]), float(props["lon"]))
        if any(_dist_m(pt, (p["lat"], p["lon"])) < MIN_SPACING_M for p in pois):
            continue
        seen.add(name.casefold())
        pois.append({"name": name, "lat": pt[0], "lon": pt[1]})
        if len(pois) >= PER_CATEGORY:
            break
    return pois


async def _fetch_category(client: httpx.AsyncClient, center: tuple[float, float], category: str) -> list[dict]:
    lat, lon = center
    key = (round(lat, 2), round(lon, 2), category)
    if key in _cache:
        return _cache[key]

    params = {
        "categories": CATEGORY_MAP[category],
        # Geoapify filter/bias-da sıra lon,lat-dır
        "filter": f"circle:{lon},{lat},{RADIUS_M}",
        "bias": f"proximity:{lon},{lat}",
        "limit": POOL_LIMIT,
        "apiKey": settings.geoapify_api_key,
    }
    try:
        resp = await client.get(GEOAPIFY_URL, params=params)
        features = resp.json().get("features", []) if resp.status_code == 200 else []
        if resp.status_code != 200:
            logger.warning("Geoapify xətası (%s): HTTP %s", category, resp.status_code)
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Geoapify xətası (%s): %s", category, e)
        features = []

    pois = _select(features)
    _cache[key] = pois
    return pois


async def fetch_pois(center: tuple[float, float], interests: list[str]) -> dict[str, list[dict]]:
    """Hər maraq kateqoriyası üçün real POI siyahısı qaytarır; açar yoxdursa və ya xəta olsa {} / boş siyahı."""
    if not settings.geoapify_api_key:
        return {}
    categories = [c for c in (i.lower().strip() for i in interests) if c in CATEGORY_MAP] or DEFAULT_CATEGORIES
    result: dict[str, list[dict]] = {}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for cat in categories:
                pois = await _fetch_category(client, center, cat)
                if pois:
                    result[cat] = pois
    except httpx.HTTPError as e:
        logger.warning("Geoapify ümumi xəta: %s", e)
    return result
