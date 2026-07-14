"""Valyuta məzənnələri servisi və endpoint-i."""

import httpx
import pytest

from app.services import rates as rates_module
from app.services.cache import KVCache
from tests.conftest import register_user

OK_BODY = {"result": "success", "rates": {"USD": 1, "EUR": 0.88, "AZN": 1.70, "TRY": 41.0}}


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(rates_module, "_cache", KVCache("rates", persist=False))


def patch_transport(monkeypatch, handler):
    real_client = httpx.AsyncClient
    counter = {"requests": 0}

    def counting_handler(request):
        counter["requests"] += 1
        return handler(request)

    def factory(**kwargs):
        return real_client(transport=httpx.MockTransport(counting_handler))

    monkeypatch.setattr(rates_module.httpx, "AsyncClient", factory)
    return counter


async def test_returns_supported_subset(monkeypatch):
    patch_transport(monkeypatch, lambda r: httpx.Response(200, json=OK_BODY))
    result = await rates_module.get_rates("USD")
    assert result == {"EUR": 0.88, "AZN": 1.70}  # TRY süzülür, base daxil deyil


async def test_cache_prevents_second_request(monkeypatch):
    counter = patch_transport(monkeypatch, lambda r: httpx.Response(200, json=OK_BODY))
    await rates_module.get_rates("USD")
    await rates_module.get_rates("USD")
    assert counter["requests"] == 1


async def test_error_returns_none_and_not_cached(monkeypatch):
    counter = patch_transport(monkeypatch, lambda r: httpx.Response(500, json={}))
    assert await rates_module.get_rates("USD") is None
    assert await rates_module.get_rates("USD") is None
    assert counter["requests"] == 2  # xəta cache-lənmir


async def test_unsupported_base_returns_none():
    assert await rates_module.get_rates("XYZ") is None


async def test_endpoint_requires_auth(client):
    resp = await client.get("/api/rates?base=USD")
    assert resp.status_code == 401


async def test_endpoint_validates_base(client, monkeypatch):
    headers = await register_user(client, email="rates@example.com")
    resp = await client.get("/api/rates?base=GBP", headers=headers)
    assert resp.status_code == 422


async def test_endpoint_success(client, monkeypatch):
    headers = await register_user(client, email="rates2@example.com")

    async def fake_rates(base):
        return {"EUR": 0.9, "AZN": 1.7}

    monkeypatch.setattr("app.routers.rates.get_rates", fake_rates)
    resp = await client.get("/api/rates?base=usd", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"base": "USD", "rates": {"EUR": 0.9, "AZN": 1.7}}
