"""Logistics Agent hesablamaları — məsafə/vaxt tam kodda."""

from app.agents import logistics

from .conftest import make_item


def test_haversine_known_pair():
    # ekvator boyu 1° uzunluq ≈ 111.19 km
    km = logistics.haversine_km((0.0, 0.0), (0.0, 1.0))
    assert abs(km - 111.19) < 0.5


def test_travel_minutes_walk_vs_transport():
    # ~1.1 km → piyada: 1.1/4*60 ≈ 17 dəq
    walk = logistics.travel_minutes((0.0, 0.0), (0.01, 0.0))
    assert 10 <= walk <= 20
    # ~111 km → nəqliyyat: 111/25*60 + 15 ≈ 282 dəq
    transport = logistics.travel_minutes((0.0, 0.0), (1.0, 0.0))
    assert transport > 250


def test_day_within_limit_approved():
    days = [{"day": 1, "items": [
        make_item(duration_min=120, lat=41.90, lon=12.49),
        make_item(name="Pantheon", duration_min=120, lat=41.899, lon=12.477),
    ]}]
    ok, stats, objs = logistics.check(days)
    assert ok is True
    assert objs == []
    assert stats[0]["active_min"] == 240


def test_day_over_limit_objects_farthest():
    # 3 x 250 dəq = 750 dəq > 720; "Far" digərlərindən aralıdadır
    days = [{"day": 1, "items": [
        make_item(name="A", duration_min=250, lat=41.90, lon=12.49),
        make_item(name="B", duration_min=250, lat=41.901, lon=12.492),
        make_item(name="Far", duration_min=250, lat=42.5, lon=13.2),
    ]}]
    ok, _, objs = logistics.check(days)
    assert ok is False
    assert objs[0]["name"] == "Far"
    assert objs[0]["day"] == 1


def test_day_without_coords_never_objected():
    # koordinatsız item-lar yol vaxtına daxil olmur, <2 located → etiraz yoxdur
    days = [{"day": 1, "items": [
        make_item(name="X", duration_min=400),
        make_item(name="Y", duration_min=400),
    ]}]
    ok, stats, objs = logistics.check(days)
    assert ok is True
    assert stats[0]["travel_min"] == 0
