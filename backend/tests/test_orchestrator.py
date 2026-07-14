"""Orchestrator negotiation axını — LLM və HTTP tam mock-lanır."""

from datetime import date

import pytest
from sqlalchemy import select

from app import orchestrator as orch
from app.models import AgentMessage, Itinerary, Trip

from .conftest import make_item

CENTER = (41.9, 12.5)


def make_trip(budget=1000.0):
    return Trip(
        city="Rome",
        start_date=date(2026, 7, 20),
        end_date=date(2026, 7, 21),
        budget=budget,
        currency="USD",
        travelers=1,
        interests=["history"],
        language="en",
    )


def cheap_days():
    return [
        {"day": 1, "items": [
            make_item(name="Colosseum", est_cost=20, lat=41.90, lon=12.49),
            make_item(name="Pantheon", est_cost=10, lat=41.899, lon=12.477),
        ]},
        {"day": 2, "items": [make_item(name="Trevi", est_cost=5, lat=41.901, lon=12.483)]},
    ]


@pytest.fixture
def patched(monkeypatch):
    async def fake_geocode(name, city=""):
        return CENTER

    async def fake_geocode_near(name, center):
        return None

    async def fake_fetch_pois(center, interests):
        return {}

    async def fake_get_daily(lat, lon, start, end):
        return [{"code": 61, "t_max": 24, "t_min": 15, "precip": 70}, None]

    async def fake_summary(trip, schedule, total_cost):
        return "final say", None

    async def fake_budget_obj(trip, total, objections):
        return "budget objection", None

    async def fake_logistics_obj(city, objections, lang="en"):
        return "logistics objection", None

    monkeypatch.setattr(orch, "geocode", fake_geocode)
    monkeypatch.setattr(orch, "geocode_near", fake_geocode_near)
    monkeypatch.setattr(orch, "fetch_pois", fake_fetch_pois)
    monkeypatch.setattr(orch, "get_daily", fake_get_daily)
    monkeypatch.setattr(orch.planner, "summary_message", fake_summary)
    monkeypatch.setattr(orch.budget, "objection_message", fake_budget_obj)
    monkeypatch.setattr(orch.logistics, "objection_message", fake_logistics_obj)
    return monkeypatch


async def roles(session, trip_id):
    result = await session.execute(
        select(AgentMessage).where(AgentMessage.trip_id == trip_id).order_by(AgentMessage.id)
    )
    return [(m.agent, m.role) for m in result.scalars().all()]


async def test_happy_path(session, patched):
    captured = {}

    async def fake_propose(trip, num_days, pois=None, weather_text=""):
        captured["weather_text"] = weather_text
        return "my proposal", cheap_days(), 80.0, None

    patched.setattr(orch.interest, "propose", fake_propose)

    trip = make_trip()
    session.add(trip)
    await session.commit()
    await orch._run(session, trip)

    rs = await roles(session, trip.id)
    assert ("interest", "proposal") in rs
    assert ("budget", "approval") in rs
    assert ("logistics", "approval") in rs
    assert ("planner", "final") in rs
    assert not any(r == "objection" for _, r in rs)

    itin = (await session.execute(select(Itinerary).where(Itinerary.trip_id == trip.id))).scalar_one()
    # aktivliklər 35 + otel (1 gecə × 1 otaq × 80) = 115
    assert itin.total_cost == 115.0
    assert itin.lodging == {"nightly": 80.0, "nights": 1, "rooms": 1, "total": 80.0}
    assert trip.status == "done"

    # hava: gün 1 proqnozla saxlanılır, gün 2 None; precip 70 → yağış hint-i prompt-a gedir
    assert itin.days[0]["weather"] == {"code": 61, "t_max": 24, "t_min": 15, "precip": 70}
    assert itin.days[1]["weather"] is None
    assert "day(s) 1" in captured["weather_text"]


async def test_over_budget_triggers_revision(session, patched):
    expensive = [{"day": 1, "items": [make_item(name="Expensive", est_cost=500, lat=41.90, lon=12.49)]},
                 {"day": 2, "items": [make_item(name="Trevi", est_cost=5, lat=41.901, lon=12.483)]}]

    async def fake_propose(trip, num_days, pois=None, weather_text=""):
        return "proposal", expensive, None, None

    async def fake_revise(trip, days, objections, pois=None):
        return "revised", cheap_days(), None

    patched.setattr(orch.interest, "propose", fake_propose)
    patched.setattr(orch.interest, "revise", fake_revise)

    trip = make_trip(budget=100.0)
    session.add(trip)
    await session.commit()
    await orch._run(session, trip)

    rs = await roles(session, trip.id)
    assert ("budget", "objection") in rs
    assert ("interest", "revision") in rs
    assert ("planner", "final") in rs
    assert trip.status == "done"


async def test_geocode_days_rejects_far_and_uses_llm_fallback(monkeypatch):
    far = (45.0, 15.0)  # mərkəzdən >80 km

    async def fake_geocode(name, city=""):
        return far

    async def fake_geocode_near(name, center):
        return None

    monkeypatch.setattr(orch, "geocode", fake_geocode)
    monkeypatch.setattr(orch, "geocode_near", fake_geocode_near)

    days = [{"day": 1, "items": [make_item(llm_lat=41.91, llm_lon=12.51)]}]
    await orch._geocode_days(days, "Rome", CENTER)
    item = days[0]["items"][0]
    # uzaq Nominatim nəticəsi rədd edilir, yaxın LLM koordinatı qəbul olunur
    assert (item["lat"], item["lon"]) == (41.91, 12.51)


async def test_apply_poi_coords_matches_casefold():
    days = [{"day": 1, "items": [make_item(name="Colosseum ")]}]
    orch._apply_poi_coords(days, {"history": [{"name": "colosseum", "lat": 41.89, "lon": 12.49}]})
    assert days[0]["items"][0]["lat"] == 41.89


async def test_apply_poi_coords_attaches_wiki():
    days = [{"day": 1, "items": [make_item(name="Trevi"), make_item(name="Naməlum")]}]
    pois = {"history": [{"name": "trevi", "lat": 41.9, "lon": 12.48, "wiki": "it:Fontana di Trevi"}]}
    orch._apply_poi_coords(days, pois)
    assert days[0]["items"][0]["wiki"] == "it:Fontana di Trevi"
    assert "wiki" not in days[0]["items"][1]
