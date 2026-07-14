"""Budget Agent hesablamaları — LLM-siz, tam deterministik."""

from datetime import date

from app.agents import budget
from app.models import Trip

from .conftest import make_item


def make_trip(budget_amount=100.0, travelers=1, currency="USD", language="en", nights=1):
    return Trip(
        budget=budget_amount, travelers=travelers, currency=currency, language=language,
        start_date=date(2026, 7, 20), end_date=date(2026, 7, 20 + nights),
    )


def test_under_budget_approved():
    days = [{"day": 1, "items": [make_item(est_cost=30), make_item(name="Pantheon", est_cost=20)]}]
    ok, total, objs = budget.check(make_trip(100.0), days)
    assert ok is True
    assert total == 50.0
    assert objs == []


def test_over_budget_objects_most_expensive_first():
    days = [
        {"day": 1, "items": [make_item(name="Cheap", est_cost=10), make_item(name="Expensive", est_cost=90)]},
    ]
    ok, total, objs = budget.check(make_trip(50.0), days)
    assert ok is False
    assert total == 100.0
    assert objs[0]["name"] == "Expensive"
    assert objs[0]["day"] == 1


def test_travelers_multiply_total():
    days = [{"day": 1, "items": [make_item(est_cost=30)]}]
    ok, total, _ = budget.check(make_trip(100.0, travelers=3), days)
    assert total == 90.0
    assert ok is True


def test_objections_capped_at_four():
    items = [make_item(name=f"Place{i}", est_cost=100) for i in range(6)]
    days = [{"day": 1, "items": items}]
    ok, _, objs = budget.check(make_trip(10.0), days)
    assert ok is False
    assert len(objs) <= 4


def test_min_target_cost_floor_in_reason():
    # 0.4 * 8 = 3.2 → MIN_TARGET_COST (5.0) döşəməsi işləməlidir
    days = [{"day": 1, "items": [make_item(name="Cheap", est_cost=8)]}]
    ok, _, objs = budget.check(make_trip(1.0), days)
    assert ok is False
    assert "5" in objs[0]["reason"]


def test_approval_message_localized():
    trip = make_trip(100.0, language="az")
    msg = budget.approval_message(trip, 50.0)
    assert "büdcə" in msg.lower() or "Büdcə" in msg


def test_lodging_block_math():
    # 2 gecə, 3 nəfər → 2 otaq: 80 × 2 × 2 = 320
    block = budget.lodging_block(make_trip(travelers=3, nights=2), 80.0)
    assert block == {"nightly": 80.0, "nights": 2, "rooms": 2, "total": 320.0}


def test_lodging_block_same_day_trip_returns_none():
    assert budget.lodging_block(make_trip(nights=0), 80.0) is None


def test_lodging_included_in_total():
    days = [{"day": 1, "items": [make_item(est_cost=30)]}]
    lodging = {"nightly": 60.0, "nights": 1, "rooms": 1, "total": 60.0}
    ok, total, _ = budget.check(make_trip(100.0), days, lodging=lodging)
    assert total == 90.0
    assert ok is True


def test_lodging_pushes_over_budget_objections_target_items():
    days = [{"day": 1, "items": [make_item(name="Museum", est_cost=30)]}]
    lodging = {"nightly": 80.0, "nights": 1, "rooms": 1, "total": 80.0}
    ok, total, objs = budget.check(make_trip(100.0), days, lodging=lodging)
    assert ok is False
    assert total == 110.0
    assert objs[0]["name"] == "Museum"  # etirazlar yalnız item-lara yönəlir


def test_approval_message_mentions_lodging():
    trip = make_trip(200.0)
    lodging = {"nightly": 60.0, "nights": 1, "rooms": 1, "total": 60.0}
    msg = budget.approval_message(trip, 90.0, lodging)
    assert "60.0" in msg
