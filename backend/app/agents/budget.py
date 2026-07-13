"""Budget Agent: xərc hesablanması kodda aparılır, LLM yalnız qısa etiraz mesajı üçün istifadə olunur."""

from ..llm import prompts
from ..llm.client import LLMResult
from ..models import Trip
from .base import ask_text

MIN_TARGET_COST = 5.0


def check(trip: Trip, days: list[dict]) -> tuple[bool, float, list[dict]]:
    """(uyğundur?, ümumi xərc, etirazlar). Ən bahalı item-lar aşım qapanana qədər etiraz alır."""
    travelers = trip.travelers
    budget = float(trip.budget)
    total = round(sum(i["est_cost"] for d in days for i in d["items"]) * travelers, 2)
    if total <= budget:
        return True, total, []

    overshoot = total - budget
    flat = sorted(
        ((d["day"], i) for d in days for i in d["items"]),
        key=lambda x: -x[1]["est_cost"],
    )
    objections, saved = [], 0.0
    for day_no, item in flat:
        if saved >= overshoot or len(objections) >= 4:
            break
        target = max(round(item["est_cost"] * 0.4), MIN_TARGET_COST)
        objections.append(
            {
                "day": day_no,
                "name": item["name"],
                "reason": prompts.msg(
                    trip.language, "budget_reason",
                    cost=item["est_cost"], cur=trip.currency, target=target,
                ),
            }
        )
        saved += (item["est_cost"] - target) * travelers
    return False, total, objections


def approval_message(trip: Trip, total: float) -> str:
    return prompts.msg(trip.language, "budget_ok", total=total, budget=float(trip.budget), cur=trip.currency)


async def objection_message(trip: Trip, total: float, objections: list[dict]) -> tuple[str, LLMResult | None]:
    facts = (
        f"Budget: {float(trip.budget)} {trip.currency} ({trip.travelers} travelers). Calculated total: {total} {trip.currency}. "
        "Objected items: " + "; ".join(f'Day {o["day"]} — {o["name"]} ({o["reason"]})' for o in objections)
    )
    try:
        return await ask_text(prompts.budget_say_system(trip.language), facts)
    except Exception:
        # LLM əlçatan olmasa danışıq template ilə davam edir
        items = "; ".join(f'Day {o["day"]}: "{o["name"]}" — {o["reason"]}' for o in objections)
        return (
            prompts.msg(
                trip.language, "budget_obj_template",
                total=total, budget=float(trip.budget), cur=trip.currency, items=items,
            ),
            None,
        )
