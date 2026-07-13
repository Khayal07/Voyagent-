"""Interest Agent: maraqlara uyğun aktivlik namizədləri təklif edir və etirazlara cavab verir."""

from ..llm import prompts
from ..llm.client import LLMResult
from ..models import Trip
from .base import AgentError, ask_json

VALID_CATEGORIES = {"history", "nature", "food", "nightlife", "art", "shopping", "other"}


def _normalize_item(raw: dict) -> dict | None:
    try:
        cat = str(raw.get("category", "other")).lower()
        return {
            "name": str(raw["name"]).strip()[:120],
            "category": cat if cat in VALID_CATEGORIES else "other",
            "est_cost": max(0.0, round(float(raw.get("est_cost", 0)), 2)),
            "duration_min": min(600, max(15, int(raw.get("duration_min", 90)))),
            "lat": None,
            "lon": None,
        }
    except (KeyError, TypeError, ValueError):
        return None


def normalize_days(raw_days: list, num_days: int) -> list[dict]:
    days = []
    for d in range(1, num_days + 1):
        found = next((x for x in raw_days if int(x.get("day", 0) or 0) == d), None)
        items = [i for i in ((_normalize_item(r) for r in (found or {}).get("items", [])[:4])) if i]
        days.append({"day": d, "items": items})
    if not any(d["items"] for d in days):
        raise AgentError("Interest Agent heç bir aktivlik qaytarmadı")
    return days


async def propose(trip: Trip, num_days: int) -> tuple[str, list[dict], LLMResult]:
    data, llm = await ask_json(
        prompts.INTEREST_SYSTEM,
        prompts.interest_propose(trip.city, num_days, list(trip.interests or []), trip.travelers, trip.currency),
        max_tokens=1200,
    )
    say = str(data.get("say", "Təkliflərim hazırdır.")).strip()
    return say, normalize_days(data.get("days", []), num_days), llm


async def revise(trip: Trip, days: list[dict], objections: list[dict]) -> tuple[str, list[dict], LLMResult]:
    """Yalnız etiraz olunan item-ları əvəz edir; days siyahısının yenilənmiş kopyasını qaytarır."""
    data, llm = await ask_json(
        prompts.INTEREST_SYSTEM,
        prompts.interest_revise(trip.city, trip.currency, objections),
        max_tokens=800,
    )
    say = str(data.get("say", "Alternativlər təklif edirəm.")).strip()

    new_days = [{"day": d["day"], "items": list(d["items"])} for d in days]
    for rep in data.get("replacements", []):
        item = _normalize_item(rep.get("item", {}))
        if item is None:
            continue
        try:
            day_no = int(rep.get("day", 0))
            old_name = str(rep.get("replace", "")).strip().lower()
        except (TypeError, ValueError):
            continue
        for d in new_days:
            if d["day"] != day_no:
                continue
            # eyni gündə dublikat yer yaranmasın
            if any(x["name"].lower() == item["name"].lower() for x in d["items"]):
                break
            for idx, existing in enumerate(d["items"]):
                if existing["name"].lower() == old_name:
                    d["items"][idx] = item
                    break
            else:
                # ad tam uyğun gəlməsə, etiraz olunan item-ı adına görə tapmağa çalışırıq
                obj_names = {o["name"].lower() for o in objections if o["day"] == day_no}
                for idx, existing in enumerate(d["items"]):
                    if existing["name"].lower() in obj_names:
                        d["items"][idx] = item
                        break
    return say, new_days, llm
