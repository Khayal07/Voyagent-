"""Trips API: yaratma, validasiya, 404, sahiblik, SSE replay və itinerary redaktəsi."""

import uuid
from datetime import date

from app.models import AgentMessage, Itinerary, Trip

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


# ---- PATCH /api/trips/{id}/itinerary ----

LODGING = {"nightly": 80.0, "nights": 1, "rooms": 1, "total": 80.0}
WEATHER_D1 = {"code": 61, "t_max": 24, "t_min": 15, "precip": 70}


def sched_item(name, cost=10.0, start="09:30"):
    return {
        "name": name, "category": "history", "est_cost": cost, "duration_min": 60,
        "lat": 41.9, "lon": 12.5, "start_time": start, "wiki": f"en:{name}",
    }


async def make_planned_trip(session, user_id, status="done"):
    trip = Trip(
        city="Rome", start_date=date(2026, 7, 20), end_date=date(2026, 7, 21),
        budget=500.0, currency="USD", travelers=1, interests=[], language="en",
        status=status, user_id=user_id,
    )
    session.add(trip)
    await session.commit()
    itin = Itinerary(
        trip_id=trip.id,
        days=[
            {"day": 1, "date": "2026-07-20", "weather": WEATHER_D1,
             "items": [sched_item("Colosseum", 20.0), sched_item("Pantheon", 10.0, "11:00")]},
            {"day": 2, "date": "2026-07-21", "weather": None,
             "items": [sched_item("Trevi", 5.0)]},
        ],
        total_cost=115.0,  # 35 aktivlik + 80 otel
        lodging=LODGING,
    )
    session.add(itin)
    await session.commit()
    return trip


async def test_patch_reorder_recomputes_times(client, session):
    headers = await register_user(client)
    trip = await make_planned_trip(session, await owner_id(client, headers))
    body = {"days": [{"day": 1, "items": ["Pantheon", "Colosseum"]}, {"day": 2, "items": ["Trevi"]}]}
    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    d1 = data["days"][0]["items"]
    assert [i["name"] for i in d1] == ["Pantheon", "Colosseum"]
    assert d1[0]["start_time"] == "09:30"  # cədvəl yenidən qurulur
    assert data["total_cost"] == 115.0  # xərc dəyişmir
    assert data["days"][0]["weather"] == WEATHER_D1  # hava qorunur
    assert d1[0]["wiki"] == "en:Pantheon"  # wiki qorunur


async def test_patch_move_across_days(client, session):
    headers = await register_user(client)
    trip = await make_planned_trip(session, await owner_id(client, headers))
    body = {"days": [{"day": 1, "items": ["Colosseum"]}, {"day": 2, "items": ["Trevi", "Pantheon"]}]}
    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body, headers=headers)
    assert resp.status_code == 200
    assert [i["name"] for i in resp.json()["days"][1]["items"]] == ["Trevi", "Pantheon"]


async def test_patch_delete_item_drops_total_keeps_lodging(client, session):
    headers = await register_user(client)
    trip = await make_planned_trip(session, await owner_id(client, headers))
    body = {"days": [{"day": 1, "items": ["Pantheon"]}, {"day": 2, "items": ["Trevi"]}]}
    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost"] == 95.0  # 15 aktivlik + 80 otel
    assert data["lodging"] == LODGING


async def test_patch_validation_422(client, session):
    headers = await register_user(client)
    trip = await make_planned_trip(session, await owner_id(client, headers))
    cases = [
        {"days": [{"day": 1, "items": ["Yad Yer"]}, {"day": 2, "items": ["Trevi"]}]},  # naməlum ad
        {"days": [{"day": 1, "items": ["Trevi"]}, {"day": 2, "items": ["Trevi"]}]},  # dublikat
        {"days": [{"day": 1, "items": ["Colosseum"]}]},  # yanlış gün dəsti
        {"days": [{"day": 1, "items": []}, {"day": 2, "items": []}]},  # boş plan
    ]
    for body in cases:
        resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body, headers=headers)
        assert resp.status_code == 422, body


async def test_patch_allows_same_place_on_two_days(client, session):
    """Eyni yer planda iki gündə varsa, təkrar saxlanışda 422 olmamalıdır (regresiya)."""
    headers = await register_user(client)
    user_id = await owner_id(client, headers)
    trip = Trip(
        city="Rome", start_date=date(2026, 7, 20), end_date=date(2026, 7, 21),
        budget=500.0, currency="USD", travelers=1, interests=[], language="en",
        status="done", user_id=user_id,
    )
    session.add(trip)
    await session.commit()
    itin = Itinerary(
        trip_id=trip.id,
        days=[
            {"day": 1, "date": "2026-07-20", "weather": None, "items": [sched_item("Trevi", 5.0)]},
            {"day": 2, "date": "2026-07-21", "weather": None, "items": [sched_item("Trevi", 5.0)]},
        ],
        total_cost=90.0, lodging=LODGING,
    )
    session.add(itin)
    await session.commit()

    body = {"days": [{"day": 1, "items": ["Trevi"]}, {"day": 2, "items": ["Trevi"]}]}
    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body, headers=headers)
    assert resp.status_code == 200
    # Eyni adı ikidən çox istifadə etmək (mövcud sayı aşmaq) yenə də bloklanır
    over = {"days": [{"day": 1, "items": ["Trevi", "Trevi"]}, {"day": 2, "items": ["Trevi"]}]}
    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=over, headers=headers)
    assert resp.status_code == 422


async def test_patch_ownership_and_status(client, session):
    headers_a = await register_user(client, email="a@example.com")
    headers_b = await register_user(client, email="b@example.com")
    trip = await make_planned_trip(session, await owner_id(client, headers_a))
    body = {"days": [{"day": 1, "items": ["Colosseum", "Pantheon"]}, {"day": 2, "items": ["Trevi"]}]}

    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body, headers=headers_b)
    assert resp.status_code == 404  # özgə trip
    resp = await client.patch(f"/api/trips/{trip.id}/itinerary", json=body)
    assert resp.status_code == 401  # auth-suz

    planning = await make_planned_trip(session, await owner_id(client, headers_a), status="planning")
    resp = await client.patch(f"/api/trips/{planning.id}/itinerary", json=body, headers=headers_a)
    assert resp.status_code == 409  # plan hazır deyil
