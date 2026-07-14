"""Geoapify POI servisi: MockTransport ilə."""

import httpx
import pytest

from app.config import settings
from app.services import poi
from app.services.cache import KVCache


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(poi, "_cache", KVCache("poi", persist=False))
    monkeypatch.setattr(settings, "geoapify_api_key", "test-key")


def patch_transport(monkeypatch, handler):
    real_client = httpx.AsyncClient
    counter = {"requests": 0}

    def counting_handler(request):
        counter["requests"] += 1
        return handler(request)

    def factory(**kwargs):
        return real_client(transport=httpx.MockTransport(counting_handler))

    monkeypatch.setattr(poi.httpx, "AsyncClient", factory)
    return counter


def feature(name, lat=41.9, lon=12.5, raw=None, details=None):
    props = {"name": name, "lat": lat, "lon": lon}
    if raw:
        props["datasource"] = {"raw": raw}
    if details:
        props["details"] = details
    return {"properties": props}


def spread(feats):
    """Hər feature-ə fərqli lon verir ki, spacing filtri işə düşməsin."""
    for i, f in enumerate(feats):
        f["properties"]["lon"] = 12.5 + i * 0.01
    return feats


async def test_no_api_key_returns_empty(monkeypatch):
    monkeypatch.setattr(settings, "geoapify_api_key", "")
    assert await poi.fetch_pois((41.9, 12.5), ["history"]) == {}


async def test_category_mapping_in_request(monkeypatch):
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"features": [feature("Colosseum")]})

    patch_transport(monkeypatch, handler)
    result = await poi.fetch_pois((41.9, 12.5), ["history"])
    assert seen["params"]["categories"] == poi.CATEGORY_MAP["history"]
    assert seen["params"]["filter"].startswith("circle:12.5,41.9,")
    assert result["history"][0]["name"] == "Colosseum"


async def test_unnamed_and_duplicate_features_filtered(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"features": spread([
            feature("Colosseum"), feature(""), feature("colosseum"), feature("Pantheon"),
        ])})

    patch_transport(monkeypatch, handler)
    result = await poi.fetch_pois((41.9, 12.5), ["history"])
    assert [p["name"] for p in result["history"]] == ["Colosseum", "Pantheon"]


async def test_api_error_returns_empty(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(500, json={}))
    assert await poi.fetch_pois((41.9, 12.5), ["history"]) == {}


async def test_unknown_interest_falls_back_to_defaults(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": [feature("X")]}))
    result = await poi.fetch_pois((41.9, 12.5), ["unknown-interest"])
    assert set(result.keys()) == set(poi.DEFAULT_CATEGORIES)


async def test_cache_prevents_second_request(monkeypatch):
    counter = patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": [feature("X")]}))
    await poi.fetch_pois((41.9, 12.5), ["history"])
    await poi.fetch_pois((41.9, 12.5), ["history"])
    assert counter["requests"] == 1


async def test_per_category_cap(monkeypatch):
    feats = spread([feature(f"Place {i}") for i in range(poi.PER_CATEGORY + 2)])
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": feats}))
    result = await poi.fetch_pois((41.9, 12.5), ["history"])
    assert len(result["history"]) == poi.PER_CATEGORY


async def test_fame_ranking_prefers_wiki_and_translations(monkeypatch):
    feats = spread([
        feature("Obscure Alley"),
        feature("Trevi Fountain", raw={"wikipedia": "it:Fontana di Trevi"}),
        feature("Colosseum", raw={"name:en": "x", "name:az": "y", "name:fr": "z"}),
        feature("Minor Statue"),
    ])
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": feats}))
    result = await poi.fetch_pois((41.9, 12.5), ["history"])
    names = [p["name"] for p in result["history"]]
    assert names[0] == "Colosseum"
    assert names[1] == "Trevi Fountain"


async def test_min_spacing_drops_clustered_pois(monkeypatch):
    # İkisi eyni nöqtədə (Forum mikro-abidələri), üçüncüsü uzaqda
    feats = [
        feature("Temple A", lat=41.9, lon=12.5, raw={"name:en": "a"}),
        feature("Temple B", lat=41.9, lon=12.5001, raw={"name:en": "b"}),
        feature("Far Basilica", lat=41.9, lon=12.6),
    ]
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": feats}))
    result = await poi.fetch_pois((41.9, 12.5), ["history"])
    names = [p["name"] for p in result["history"]]
    assert "Temple A" in names
    assert "Temple B" not in names
    assert "Far Basilica" in names


async def test_brand_chains_rank_last(monkeypatch):
    # Starbucks kimi şəbəkələr çox name:* tərcüməsinə malikdir — brand tagı cəzalandırılır
    feats = spread([
        feature("Starbucks", raw={"brand": "Starbucks", "name:en": "a", "name:az": "b", "name:fr": "c"}),
        feature("Local Bistro"),
    ])
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": feats}))
    result = await poi.fetch_pois((41.9, 12.5), ["food"])
    assert [p["name"] for p in result["food"]] == ["Local Bistro", "Starbucks"]


async def test_request_has_proximity_bias_and_pool_limit(monkeypatch):
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"features": []})

    patch_transport(monkeypatch, handler)
    await poi.fetch_pois((41.9, 12.5), ["history"])
    assert seen["params"]["bias"] == "proximity:12.5,41.9"
    assert seen["params"]["limit"] == str(poi.POOL_LIMIT)
