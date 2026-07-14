"""Interest Agent: normalizasiya və revise əvəzetmə məntiqi (ask_json mock-lanır)."""

import pytest

from app.agents import interest
from app.agents.base import AgentError
from app.models import Trip

from .conftest import make_item


def test_normalize_item_clamps_values():
    item = interest._normalize_item(
        {"name": "  X  ", "category": "FOOD", "est_cost": -5, "duration_min": 5000, "lat": 41.9, "lon": 12.5}
    )
    assert item["name"] == "X"
    assert item["category"] == "food"
    assert item["est_cost"] == 0.0
    assert item["duration_min"] == 600
    # LLM koordinatı ayrıca saxlanılır, lat/lon boş başlayır
    assert item["lat"] is None and item["llm_lat"] == 41.9


def test_normalize_item_invalid_category_and_missing_name():
    assert interest._normalize_item({"name": "X", "category": "spa"})["category"] == "other"
    assert interest._normalize_item({"category": "food"}) is None


def test_normalize_days_fills_missing_days():
    days = interest.normalize_days([{"day": 2, "items": [{"name": "X"}]}], 3)
    assert [d["day"] for d in days] == [1, 2, 3]
    assert days[0]["items"] == [] and len(days[1]["items"]) == 1


def test_normalize_days_all_empty_raises():
    with pytest.raises(AgentError):
        interest.normalize_days([], 2)


def make_trip():
    return Trip(city="Rome", budget=100.0, travelers=1, currency="USD", language="en", interests=[])


def test_parse_hotel_nightly():
    assert interest._parse_hotel_nightly(85.5) == 85.5
    assert interest._parse_hotel_nightly("120") == 120.0
    assert interest._parse_hotel_nightly(None) is None
    assert interest._parse_hotel_nightly("bahalı") is None
    assert interest._parse_hotel_nightly(0) is None
    assert interest._parse_hotel_nightly(99999) is None


async def test_propose_returns_hotel_estimate(monkeypatch):
    async def fake_ask_json(system, user, max_tokens, temperature=0.7):
        return {
            "say": "ok",
            "days": [{"day": 1, "items": [{"name": "Colosseum"}]}],
            "hotel_nightly_est": 95,
        }, None

    monkeypatch.setattr(interest, "ask_json", fake_ask_json)
    say, days, hotel_nightly, _ = await interest.propose(make_trip(), 1)
    assert hotel_nightly == 95.0
    assert days[0]["items"][0]["name"] == "Colosseum"


async def test_revise_replaces_objected_item(monkeypatch):
    days = [{"day": 1, "items": [make_item(name="Expensive", est_cost=90)]}]
    objections = [{"day": 1, "name": "Expensive", "reason": "too expensive"}]

    async def fake_ask_json(system, user, max_tokens, temperature=0.7):
        return {
            "say": "ok",
            "replacements": [{"day": 1, "replace": "Expensive", "item": {"name": "Cheap", "est_cost": 5}}],
        }, None

    monkeypatch.setattr(interest, "ask_json", fake_ask_json)
    say, new_days, _ = await interest.revise(make_trip(), days, objections)
    assert new_days[0]["items"][0]["name"] == "Cheap"
    # orijinal siyahı dəyişməz qalır
    assert days[0]["items"][0]["name"] == "Expensive"


async def test_revise_fallback_match_by_objection_name(monkeypatch):
    # LLM "replace" adını səhv yazsa, etiraz adına görə tapılır
    days = [{"day": 1, "items": [make_item(name="Expensive", est_cost=90)]}]
    objections = [{"day": 1, "name": "Expensive", "reason": "too expensive"}]

    async def fake_ask_json(system, user, max_tokens, temperature=0.7):
        return {
            "say": "ok",
            "replacements": [{"day": 1, "replace": "WRONG NAME", "item": {"name": "Cheap", "est_cost": 5}}],
        }, None

    monkeypatch.setattr(interest, "ask_json", fake_ask_json)
    _, new_days, _ = await interest.revise(make_trip(), days, objections)
    assert new_days[0]["items"][0]["name"] == "Cheap"


async def test_revise_prevents_same_day_duplicate(monkeypatch):
    days = [{"day": 1, "items": [make_item(name="Pantheon", est_cost=5), make_item(name="Expensive", est_cost=90)]}]
    objections = [{"day": 1, "name": "Expensive", "reason": "too expensive"}]

    async def fake_ask_json(system, user, max_tokens, temperature=0.7):
        return {
            "say": "ok",
            "replacements": [{"day": 1, "replace": "Expensive", "item": {"name": "Pantheon", "est_cost": 5}}],
        }, None

    monkeypatch.setattr(interest, "ask_json", fake_ask_json)
    _, new_days, _ = await interest.revise(make_trip(), days, objections)
    # dublikat yaranmır — "Expensive" yerində qalır
    names = [i["name"] for i in new_days[0]["items"]]
    assert names.count("Pantheon") == 1
    assert "Expensive" in names
