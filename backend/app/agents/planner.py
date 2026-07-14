"""Planner Agent: cədvəl kodda deterministik qurulur, LLM yalnız yekun xülasə mesajı yazır."""

from datetime import timedelta

from ..llm import prompts
from ..llm.client import LLMResult
from ..models import Trip
from .base import ask_text
from .logistics import _coords, travel_minutes

DAY_START_MIN = 9 * 60 + 30
ITEM_GAP_MIN = 20
DEFAULT_TRAVEL_MIN = 30


def build_schedule(
    trip: Trip, days: list[dict], weather: list[dict | None] | None = None
) -> tuple[list[dict], float]:
    """Hər günə başlama vaxtları verir; gecə həyatı günün sonuna keçirilir."""
    result_days = []
    current_date = trip.start_date
    for idx, d in enumerate(days):
        items = sorted(d["items"], key=lambda i: i["category"] == "nightlife")
        t = DAY_START_MIN
        out, prev = [], None
        for item in items:
            if prev is not None:
                ca, cb = _coords(prev), _coords(item)
                t += travel_minutes(ca, cb) if (ca and cb) else DEFAULT_TRAVEL_MIN
            out.append({**item, "start_time": f"{(t // 60) % 24:02d}:{t % 60:02d}"})
            t += item["duration_min"] + ITEM_GAP_MIN
            prev = item
        result_days.append({
            "day": d["day"], "date": str(current_date), "items": out,
            "weather": weather[idx] if weather and idx < len(weather) else None,
        })
        current_date += timedelta(days=1)

    total_cost = round(sum(i["est_cost"] for d in days for i in d["items"]) * trip.travelers, 2)
    return result_days, total_cost


async def summary_message(trip: Trip, schedule: list[dict], total_cost: float) -> tuple[str, LLMResult | None]:
    compact = "; ".join(
        f"Day {d['day']}: " + ", ".join(i["name"] for i in d["items"]) for d in schedule
    )
    facts = (
        f"City: {trip.city}, {len(schedule)} days, {trip.travelers} travelers, "
        f"total cost ~{total_cost} {trip.currency} (budget {float(trip.budget)}). Plan: {compact}"
    )
    try:
        return await ask_text(prompts.planner_say_system(trip.language), facts, max_tokens=150)
    except Exception:
        return (
            prompts.msg(trip.language, "planner_template", days=len(schedule), total=total_cost, cur=trip.currency),
            None,
        )
