"""Oxu-yalnız paylaşma linki: token yaratma (sahiblik) və public görünüş (auth-suz)."""

from .conftest import register_user
from .test_api_trips import make_done_trip, owner_id


async def test_share_requires_auth(client, session):
    trip = await make_done_trip(session)
    resp = await client.post(f"/api/trips/{trip.id}/share")
    assert resp.status_code == 401


async def test_share_creates_idempotent_token(client, session):
    headers = await register_user(client)
    trip = await make_done_trip(session, user_id=await owner_id(client, headers))
    r1 = await client.post(f"/api/trips/{trip.id}/share", headers=headers)
    r2 = await client.post(f"/api/trips/{trip.id}/share", headers=headers)
    assert r1.status_code == 200 and r2.status_code == 200
    token = r1.json()["token"]
    assert token and token == r2.json()["token"]


async def test_share_other_users_trip_404(client, session):
    headers_a = await register_user(client, email="a@example.com")
    headers_b = await register_user(client, email="b@example.com")
    trip = await make_done_trip(session, user_id=await owner_id(client, headers_a))
    resp = await client.post(f"/api/trips/{trip.id}/share", headers=headers_b)
    assert resp.status_code == 404


async def test_shared_view_public_no_auth(client, session):
    headers = await register_user(client)
    trip = await make_done_trip(session, user_id=await owner_id(client, headers))
    token = (await client.post(f"/api/trips/{trip.id}/share", headers=headers)).json()["token"]

    resp = await client.get(f"/api/trips/shared/{token}")  # auth header YOX
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Rome" and data["status"] == "done"
    assert [m["role"] for m in data["messages"]] == ["proposal", "final"]


async def test_shared_view_bad_token_404(client):
    resp = await client.get("/api/trips/shared/yalnis-token")
    assert resp.status_code == 404


async def test_shared_view_rate_limited(client):
    """Public endpoint token enumerasiyasına qarşı IP başına məhdudlaşdırılır."""
    from app.ratelimit import share_limiter

    statuses = set()
    for _ in range(share_limiter.limit + 5):
        statuses.add((await client.get("/api/trips/shared/xxx")).status_code)
    assert 429 in statuses
