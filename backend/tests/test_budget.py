"""Budget Agent hesablamaları — LLM-siz, tam deterministik."""

from app.agents import budget
from app.models import Trip

from .conftest import make_item


def make_trip(budget_amount=100.0, travelers=1, currency="USD", language="en"):
    return Trip(budget=budget_amount, travelers=travelers, currency=currency, language=language)


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
