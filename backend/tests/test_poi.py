"""Geoapify POI servisi: MockTransport ilə."""

import httpx
import pytest

from app.config import settings
from app.services import poi


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(poi, "_cache", {})
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


def feature(name, lat=41.9, lon=12.5):
    return {"properties": {"name": name, "lat": lat, "lon": lon}}


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
        return httpx.Response(200, json={"features": [
            feature("Colosseum"), feature(""), feature("colosseum"), feature("Pantheon"),
        ]})

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
    feats = [feature(f"Place {i}") for i in range(10)]
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json={"features": feats}))
    result = await poi.fetch_pois((41.9, 12.5), ["history"])
    assert len(result["history"]) == poi.PER_CATEGORY
