"""Trips API: yaratma, validasiya, 404 və SSE replay."""

import uuid
from datetime import date

from app.models import AgentMessage, Trip

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


async def test_create_trip_201(client):
    resp = await client.post("/api/trips", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["city"] == "Rome"
    assert data["status"] == "pending"
    uuid.UUID(data["id"])


async def test_create_trip_end_before_start_422(client):
    payload = {**VALID_PAYLOAD, "end_date": "2026-07-19"}
    resp = await client.post("/api/trips", json=payload)
    assert resp.status_code == 422


async def test_create_trip_too_long_422(client):
    payload = {**VALID_PAYLOAD, "end_date": "2026-07-30"}
    resp = await client.post("/api/trips", json=payload)
    assert resp.status_code == 422


async def test_get_unknown_trip_404(client):
    resp = await client.get(f"/api/trips/{uuid.uuid4()}")
    assert resp.status_code == 404


async def make_done_trip(session):
    trip = Trip(
        city="Rome", start_date=date(2026, 7, 20), end_date=date(2026, 7, 21),
        budget=500.0, currency="USD", travelers=1, interests=[], language="en", status="done",
    )
    session.add(trip)
    await session.commit()
    session.add_all([
        AgentMessage(trip_id=trip.id, agent="interest", round=0, role="proposal", content="p1"),
        AgentMessage(trip_id=trip.id, agent="planner", round=99, role="final", content="f1"),
    ])
    await session.commit()
    return trip


async def test_get_trip_detail_includes_messages(client, session):
    trip = await make_done_trip(session)
    resp = await client.get(f"/api/trips/{trip.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert [m["role"] for m in data["messages"]] == ["proposal", "final"]


async def test_stream_replays_done_trip(client, session):
    trip = await make_done_trip(session)
    resp = await client.get(f"/api/trips/{trip.id}/stream")
    assert resp.status_code == 200
    text = resp.text
    assert "event: status" in text
    assert text.count("event: agent_message") == 2
    assert "event: done" in text


async def test_stream_unknown_trip_404(client):
    resp = await client.get(f"/api/trips/{uuid.uuid4()}/stream")
    assert resp.status_code == 404
