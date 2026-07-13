"""Logistics Agent: koordinatlara əsasən günlük marşrutun vaxta sığmasını kodda yoxlayır."""

import math

from ..llm import prompts
from ..llm.client import LLMResult
from .base import ask_text

WALK_KMH = 4.0
TRANSPORT_KMH = 25.0
WALK_MAX_KM = 2.0
TRANSPORT_OVERHEAD_MIN = 15
DAY_LIMIT_MIN = 12 * 60


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def travel_minutes(a: tuple[float, float], b: tuple[float, float]) -> int:
    km = haversine_km(a, b)
    if km <= WALK_MAX_KM:
        return round(km / WALK_KMH * 60)
    return round(km / TRANSPORT_KMH * 60) + TRANSPORT_OVERHEAD_MIN


def _coords(item: dict) -> tuple[float, float] | None:
    if item.get("lat") is not None and item.get("lon") is not None:
        return (item["lat"], item["lon"])
    return None


def check(days: list[dict]) -> tuple[bool, list[dict], list[dict]]:
    """(uyğundur?, günlük statistika, etirazlar). Sığmayan gündə ən uzaq item etiraz alır."""
    objections, stats = [], []
    for d in days:
        located = [(i, _coords(i)) for i in d["items"] if _coords(i)]
        travel_min = 0
        for (a, ca), (b, cb) in zip(located, located[1:]):
            travel_min += travel_minutes(ca, cb)
        active_min = sum(i["duration_min"] for i in d["items"])
        total_min = travel_min + active_min
        stats.append({"day": d["day"], "travel_min": travel_min, "active_min": active_min})

        if total_min > DAY_LIMIT_MIN and len(located) >= 2:
            # digərlərindən orta hesabla ən uzaq yer marşrutu pozan sayılır
            def avg_dist(entry):
                _, c = entry
                return sum(haversine_km(c, other) for _, other in located if other != c) / (len(located) - 1)

            far_item, _ = max(located, key=avg_dist)
            objections.append(
                {
                    "day": d["day"],
                    "name": far_item["name"],
                    "reason": (
                        f"gün {d['day']} cədvələ sığmır (~{round(total_min / 60, 1)} saat aktivlik+yol) — "
                        "digər yerlərə daha yaxın alternativ lazımdır"
                    ),
                }
            )
    return len(objections) == 0, stats, objections


def approval_message(stats: list[dict]) -> str:
    parts = ", ".join(f"gün {s['day']}: ~{round((s['travel_min'] + s['active_min']) / 60, 1)} saat" for s in stats)
    return f"Logistika yoxlanışı: bütün günlər real vaxta sığır ({parts}). Təsdiqləyirəm."


async def objection_message(city: str, objections: list[dict]) -> tuple[str, LLMResult | None]:
    facts = f"Şəhər: {city}. Problemlər: " + "; ".join(
        f'Gün {o["day"]} — {o["name"]}: {o["reason"]}' for o in objections
    )
    try:
        return await ask_text(prompts.LOGISTICS_SAY_SYSTEM, facts)
    except Exception:
        return "; ".join(f'Gün {o["day"]}: "{o["name"]}" — {o["reason"]}' for o in objections), None
