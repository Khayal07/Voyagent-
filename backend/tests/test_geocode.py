"""Geocode servisi: MockTransport ilə Nominatim cavabları simulyasiya olunur."""

import httpx
import pytest

from app.services import geocode as geo


class FakeTime:
    """Hər monotonic çağırışında 10s irəli gedir — rate-limit sleep-i sıfırlanır."""

    def __init__(self):
        self.t = 0.0

    def monotonic(self):
        self.t += 10.0
        return self.t


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(geo, "_cache", {})
    monkeypatch.setattr(geo, "_last_request", 0.0)
    monkeypatch.setattr(geo, "time", FakeTime())


def patch_transport(monkeypatch, handler):
    real_client = httpx.AsyncClient
    counter = {"requests": 0}

    def counting_handler(request):
        counter["requests"] += 1
        return handler(request)

    def factory(**kwargs):
        return real_client(transport=httpx.MockTransport(counting_handler))

    monkeypatch.setattr(geo.httpx, "AsyncClient", factory)
    return counter


async def test_geocode_found(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json=[{"lat": "41.9", "lon": "12.5"}]))
    assert await geo.geocode("Colosseum", "Rome") == (41.9, 12.5)


async def test_geocode_not_found_returns_none(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json=[]))
    assert await geo.geocode("Nowhere", "Rome") is None


async def test_geocode_http_error_returns_none(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("boom")

    patch_transport(monkeypatch, handler)
    assert await geo.geocode("Colosseum", "Rome") is None


async def test_geocode_cache_hit_no_second_request(monkeypatch):
    counter = patch_transport(monkeypatch, lambda r: httpx.Response(200, json=[{"lat": "1", "lon": "2"}]))
    await geo.geocode("Colosseum", "Rome")
    await geo.geocode("Colosseum", "Rome")
    assert counter["requests"] == 1


async def test_geocode_near_uses_bounded_viewbox(monkeypatch):
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=[{"lat": "41.9", "lon": "12.5"}])

    patch_transport(monkeypatch, handler)
    await geo.geocode_near("Pantheon", (41.9, 12.5))
    assert seen["params"]["bounded"] == "1"
    assert "viewbox" in seen["params"]
