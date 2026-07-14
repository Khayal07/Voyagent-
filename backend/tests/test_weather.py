"""Open-Meteo hava servisi: MockTransport + üfüq/clamp məntiqi."""

from datetime import date, timedelta

import httpx
import pytest

from app.services import weather
from app.services.cache import KVCache

TODAY = date.today()


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(weather, "_cache", KVCache("weather", persist=False))


def patch_transport(monkeypatch, handler):
    real_client = httpx.AsyncClient
    counter = {"requests": 0}

    def counting_handler(request):
        counter["requests"] += 1
        return handler(request)

    def factory(**kwargs):
        return real_client(transport=httpx.MockTransport(counting_handler))

    monkeypatch.setattr(weather.httpx, "AsyncClient", factory)
    return counter


def daily_body(n):
    return {"daily": {
        "weather_code": [61] * n,
        "temperature_2m_max": [24.6] * n,
        "temperature_2m_min": [15.2] * n,
        "precipitation_probability_max": [70] * n,
    }}


async def test_beyond_horizon_no_request(monkeypatch):
    counter = patch_transport(monkeypatch, lambda r: httpx.Response(200, json=daily_body(2)))
    start = TODAY + timedelta(days=20)
    result = await weather.get_daily(41.9, 12.5, start, start + timedelta(days=1))
    assert result == [None, None]
    assert counter["requests"] == 0


async def test_success_mapping(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json=daily_body(2)))
    result = await weather.get_daily(41.9, 12.5, TODAY, TODAY + timedelta(days=1))
    assert result == [{"code": 61, "t_max": 25, "t_min": 15, "precip": 70}] * 2


async def test_horizon_clamp_pads_none(monkeypatch):
    seen = {}

    def handler(request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=daily_body(3))

    patch_transport(monkeypatch, handler)
    # trip üfüqü 2 gün aşır → sorğu clamp olunur, quyruq None
    start = TODAY + timedelta(days=13)
    result = await weather.get_daily(41.9, 12.5, start, start + timedelta(days=4))
    assert len(result) == 5
    assert result[3] is None and result[4] is None
    assert seen["params"]["end_date"] == str(TODAY + timedelta(days=15))


async def test_http_error_returns_all_none(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(500, json={}))
    result = await weather.get_daily(41.9, 12.5, TODAY, TODAY + timedelta(days=1))
    assert result == [None, None]


async def test_cache_prevents_second_request(monkeypatch):
    counter = patch_transport(monkeypatch, lambda r: httpx.Response(200, json=daily_body(2)))
    await weather.get_daily(41.9, 12.5, TODAY, TODAY + timedelta(days=1))
    await weather.get_daily(41.9, 12.5, TODAY, TODAY + timedelta(days=1))
    assert counter["requests"] == 1
