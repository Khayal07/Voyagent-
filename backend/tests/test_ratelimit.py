"""Rate limiting: auth (IP başına) və trip yaradılması (istifadəçi başına)."""

import pytest
from fastapi import HTTPException

from app.ratelimit import RateLimiter, auth_limiter, trip_limiter
from tests.conftest import register_user

TRIP_BODY = {
    "city": "Rome",
    "start_date": "2026-08-10",
    "end_date": "2026-08-11",
    "budget": 500,
    "currency": "USD",
    "travelers": 2,
    "interests": ["history"],
    "language": "en",
}


def test_limiter_blocks_after_limit():
    rl = RateLimiter(limit=3, window_s=60)
    for _ in range(3):
        rl.check("k")
    with pytest.raises(HTTPException) as exc:
        rl.check("k")
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_limiter_keys_are_independent():
    rl = RateLimiter(limit=1, window_s=60)
    rl.check("a")
    rl.check("b")  # ayrı açar — bloklanmır


def test_limiter_window_expires(monkeypatch):
    rl = RateLimiter(limit=1, window_s=60)
    t = {"now": 0.0}
    monkeypatch.setattr("app.ratelimit.time.monotonic", lambda: t["now"])
    rl.check("k")
    t["now"] = 61.0
    rl.check("k")  # pəncərə keçib — bloklanmır


async def test_login_returns_429_after_limit(client):
    await register_user(client, email="rl@example.com")
    body = {"email": "rl@example.com", "password": "wrong-pass"}
    # register 1 hit istifadə edib
    for _ in range(auth_limiter.limit - 1):
        resp = await client.post("/api/auth/login", json=body)
        assert resp.status_code == 401
    resp = await client.post("/api/auth/login", json=body)
    assert resp.status_code == 429


async def test_trip_creation_429_after_limit(client):
    headers = await register_user(client, email="tripper@example.com")
    for _ in range(trip_limiter.limit):
        resp = await client.post("/api/trips", json=TRIP_BODY, headers=headers)
        assert resp.status_code == 201
    resp = await client.post("/api/trips", json=TRIP_BODY, headers=headers)
    assert resp.status_code == 429


async def test_trip_limit_is_per_user(client):
    h1 = await register_user(client, email="u1@example.com")
    for _ in range(trip_limiter.limit):
        await client.post("/api/trips", json=TRIP_BODY, headers=h1)
    h2 = await register_user(client, email="u2@example.com")
    resp = await client.post("/api/trips", json=TRIP_BODY, headers=h2)
    assert resp.status_code == 201
