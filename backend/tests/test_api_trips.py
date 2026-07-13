"""Trips API: yaratma, validasiya, 404, sahiblik və SSE replay."""

import uuid
from datetime import date

from app.models import AgentMessage, Trip

from .conftest import register_user

VALID_PAYLOAD = {
    "city": "Rome",
    "start_date": "2026-07-20",
    "end_date": "2026-07-22",
    "budget": 500,
    "currency": "USD",
    "travelers": 2,
    "interests": ["history", "food"],
    "language": "en",
}


async def test_create_trip_requires_auth(client):
    resp = await client.post("/api/trips", json=VALID_PAYLOAD)
    assert resp.status_code == 401


async def test_create_trip_201(client):
    headers = await register_user(client)
    resp = await client.post("/api/trips", json=VALID_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["city"] == "Rome"
    assert data["status"] == "pending"
    uuid.UUID(data["id"])


async def test_create_trip_end_before_start_422(client):
    headers = await register_user(client)
    payload = {**VALID_PAYLOAD, "end_date": "2026-07-19"}
    resp = await client.post("/api/trips", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_create_trip_too_long_422(client):
    headers = await register_user(client)
    payload = {**VALID_PAYLOAD, "end_date": "2026-07-30"}
    resp = await client.post("/api/trips", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_get_unknown_trip_404(client):
    headers = await register_user(client)
    resp = await client.get(f"/api/trips/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404


async def make_done_trip(session, user_id=None):
    trip = Trip(
        city="Rome", start_date=date(2026, 7, 20), end_date=date(2026, 7, 21),
        budget=500.0, currency="USD", travelers=1, interests=[], language="en",
        status="done", user_id=user_id,
    )
    session.add(trip)
    await session.commit()
    session.add_all([
        AgentMessage(trip_id=trip.id, agent="interest", round=0, role="proposal", content="p1"),
        AgentMessage(trip_id=trip.id, agent="planner", round=99, role="final", content="f1"),
    ])
    await session.commit()
    return trip


async def owner_id(client, headers):
    resp = await client.get("/api/auth/me", headers=headers)
    return uuid.UUID(resp.json()["id"])


async def test_get_trip_detail_includes_messages(client, session):
    headers = await register_user(client)
    trip = await make_done_trip(session, user_id=await owner_id(client, headers))
    resp = await client.get(f"/api/trips/{trip.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert [m["role"] for m in data["messages"]] == ["proposal", "final"]


async def test_other_users_trip_hidden_as_404(client, session):
    headers_a = await register_user(client, email="a@example.com")
    headers_b = await register_user(client, email="b@example.com")
    trip = await make_done_trip(session, user_id=await owner_id(client, headers_a))
    resp = await client.get(f"/api/trips/{trip.id}", headers=headers_b)
    assert resp.status_code == 404


async def test_list_trips_scoped_to_user(client, session):
    headers_a = await register_user(client, email="a@example.com")
    headers_b = await register_user(client, email="b@example.com")
    await make_done_trip(session, user_id=await owner_id(client, headers_a))
    resp_a = await client.get("/api/trips", headers=headers_a)
    resp_b = await client.get("/api/trips", headers=headers_b)
    assert len(resp_a.json()) == 1
    assert resp_b.json() == []


async def test_stream_replays_done_trip(client, session):
    headers = await register_user(client)
    trip = await make_done_trip(session, user_id=await owner_id(client, headers))
    resp = await client.get(f"/api/trips/{trip.id}/stream", headers=headers)
    assert resp.status_code == 200
    text = resp.text
    assert "event: status" in text
    assert text.count("event: agent_message") == 2
    assert "event: done" in text


async def test_stream_accepts_token_query_param(client, session):
    # EventSource header qoya bilmir — ?token= yolu
    headers = await register_user(client)
    token = headers["Authorization"].removeprefix("Bearer ")
    trip = await make_done_trip(session, user_id=await owner_id(client, headers))
    resp = await client.get(f"/api/trips/{trip.id}/stream?token={token}")
    assert resp.status_code == 200
    assert "event: done" in resp.text


async def test_stream_unknown_trip_404(client):
    headers = await register_user(client)
    resp = await client.get(f"/api/trips/{uuid.uuid4()}/stream", headers=headers)
    assert resp.status_code == 404
