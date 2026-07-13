"""Negotiation orchestrator: agentləri ardıcıl işə salır, mesajları DB-yə yazır və SSE-yə ötürür."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .agents import budget, interest, logistics, planner
from .agents.logistics import haversine_km
from .db import SessionLocal
from .events import bus
from .llm.client import LLMResult
from .llm.prompts import msg
from .models import AgentMessage, Itinerary, Trip
from .services.geocode import geocode, geocode_near
from .services.poi import fetch_pois

logger = logging.getLogger("voyagent.orchestrator")

MAX_ROUNDS = 2


async def emit(
    session: AsyncSession,
    trip_id: uuid.UUID,
    agent: str,
    round_: int,
    role: str,
    content: str,
    payload: dict | None = None,
) -> None:
    """Agent mesajını DB-yə yazır və canlı stream-ə göndərir."""
    msg = AgentMessage(trip_id=trip_id, agent=agent, round=round_, role=role, content=content, payload=payload)
    session.add(msg)
    await session.commit()
    await bus.publish(
        str(trip_id),
        "agent_message",
        {"id": msg.id, "agent": agent, "round": round_, "role": role, "content": content, "payload": payload},
    )


async def note_fallback(
    session: AsyncSession, trip_id: uuid.UUID, agent: str, round_: int, llm: LLMResult | None, lang: str = "en"
) -> None:
    """Provider fallback baş veribsə bunu şəffaf şəkildə istifadəçiyə göstərir."""
    if llm is not None and llm.fallback_reason:
        await emit(
            session, trip_id, "system", round_, "info",
            msg(lang, "fallback", agent=agent.capitalize(), model=llm.model, reason=llm.fallback_reason[:150]),
        )


async def set_status(session: AsyncSession, trip: Trip, status: str) -> None:
    trip.status = status
    await session.commit()
    await bus.publish(str(trip.id), "status", {"status": status})


MAX_KM_FROM_CENTER = 80


def _apply_poi_coords(days: list[dict], pois: dict[str, list[dict]]) -> None:
    """Geoapify namizədləri ilə ad uyğunluğu olan item-lara real koordinatı birbaşa yazır."""
    index = {p["name"].casefold().strip(): (p["lat"], p["lon"]) for items in pois.values() for p in items}
    if not index:
        return
    for d in days:
        for item in d["items"]:
            if item.get("lat") is None:
                coords = index.get(item["name"].casefold().strip())
                if coords is not None:
                    item["lat"], item["lon"] = coords


async def _geocode_days(days: list[dict], city: str, center: tuple[float, float] | None) -> None:
    """3 qatlı zəncir: 'ad, şəhər' → şəhər ətrafında bounded axtarış → LLM-in təxmini koordinatı.

    Şəhər mərkəzindən çox uzaq nəticələr (eyniadlı başqa yer) rədd edilir.
    """
    def near_center(c: tuple[float, float]) -> bool:
        return center is None or haversine_km(c, center) <= MAX_KM_FROM_CENTER

    for d in days:
        for item in d["items"]:
            if item.get("lat") is not None:
                continue
            coords = await geocode(item["name"], city)
            if coords is not None and not near_center(coords):
                logger.info("Geocode nəticəsi çox uzaqdır, rədd edildi: %s", item["name"])
                coords = None
            if coords is None and center is not None:
                coords = await geocode_near(item["name"], center)
            if coords is None and item.get("llm_lat") is not None:
                llm_coords = (item["llm_lat"], item["llm_lon"])
                if near_center(llm_coords):
                    coords = llm_coords
                    logger.info("LLM koordinatı istifadə olundu: %s", item["name"])
            if coords is not None:
                item["lat"], item["lon"] = coords


async def run_trip_planning(trip_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        trip = await session.get(Trip, trip_id)
        if trip is None:
            logger.error("Trip tapılmadı: %s", trip_id)
            return
        try:
            await _run(session, trip)
        except Exception as e:
            logger.exception("Planlaşdırma xətası (trip=%s)", trip_id)
            await session.rollback()
            await emit(session, trip_id, "system", 0, "info", msg(trip.language, "stopped", error=str(e)[:200]))
            await set_status(session, trip, "failed")
            await bus.publish(str(trip_id), "error", {"detail": str(e)[:200]})


async def _run(session: AsyncSession, trip: Trip) -> None:
    trip_id = trip.id
    lang = trip.language
    num_days = (trip.end_date - trip.start_date).days + 1
    await set_status(session, trip, "planning")
    city_coords = await geocode(trip.city)
    await emit(
        session, trip_id, "system", 0, "info",
        msg(lang, "start", city=trip.city, days=num_days),
        {"lat": city_coords[0], "lon": city_coords[1]} if city_coords else None,
    )

    # Real POI namizədləri (Geoapify) — açar yoxdursa/xəta olsa boş qalır, köhnə yol işləyir
    pois = await fetch_pois(city_coords, list(trip.interests or [])) if city_coords else {}
    if pois:
        n = sum(len(v) for v in pois.values())
        await emit(session, trip_id, "system", 0, "info", msg(lang, "poi_found", n=n, city=trip.city))

    # Raund 0: Interest Agent ilkin təklif
    say, days, llm = await interest.propose(trip, num_days, pois)
    await note_fallback(session, trip_id, "interest", 0, llm, lang)
    await emit(session, trip_id, "interest", 0, "proposal", say, {"days": days})

    await emit(session, trip_id, "system", 0, "info", msg(lang, "geocoding"))
    _apply_poi_coords(days, pois)
    await _geocode_days(days, trip.city, city_coords)

    # Negotiation dövrəsi
    for round_no in range(1, MAX_ROUNDS + 2):
        budget_ok, total, budget_objs = budget.check(trip, days)
        if budget_ok:
            await emit(session, trip_id, "budget", round_no, "approval", budget.approval_message(trip, total))
        else:
            obj_msg, b_llm = await budget.objection_message(trip, total, budget_objs)
            await note_fallback(session, trip_id, "budget", round_no, b_llm, lang)
            await emit(session, trip_id, "budget", round_no, "objection", obj_msg, {"objections": budget_objs, "total": total})

        logistics_ok, stats, logistics_objs = logistics.check(days, lang)
        if logistics_ok:
            await emit(session, trip_id, "logistics", round_no, "approval", logistics.approval_message(stats, lang))
        else:
            obj_msg, l_llm = await logistics.objection_message(trip.city, logistics_objs, lang)
            await note_fallback(session, trip_id, "logistics", round_no, l_llm, lang)
            await emit(session, trip_id, "logistics", round_no, "objection", obj_msg, {"objections": logistics_objs})

        objections = budget_objs + logistics_objs
        if not objections:
            break
        if round_no > MAX_ROUNDS:
            await emit(session, trip_id, "system", round_no, "info", msg(lang, "max_rounds"))
            break

        # Yalnız etiraz olunan item-ların kateqoriyalarına aid POI-lər (token qənaəti)
        obj_names = {o["name"].casefold() for o in objections}
        obj_cats = {i["category"] for d in days for i in d["items"] if i["name"].casefold() in obj_names}
        pois_trim = {c: pois[c] for c in obj_cats if c in pois}

        say, days, llm = await interest.revise(trip, days, objections, pois_trim)
        await note_fallback(session, trip_id, "interest", round_no, llm, lang)
        await emit(session, trip_id, "interest", round_no, "revision", say, {"days": days})
        _apply_poi_coords(days, pois)
        await _geocode_days(days, trip.city, city_coords)

    # Planner: yekun cədvəl
    schedule, total_cost = planner.build_schedule(trip, days)
    say, p_llm = await planner.summary_message(trip, schedule, total_cost)
    await note_fallback(session, trip_id, "planner", 99, p_llm, lang)
    await emit(session, trip_id, "planner", 99, "final", say, {"days": schedule, "total_cost": total_cost})

    session.add(Itinerary(trip_id=trip_id, days=schedule, total_cost=total_cost))
    await session.commit()
    await bus.publish(str(trip_id), "itinerary", {"days": schedule, "total_cost": total_cost})

    await set_status(session, trip, "done")
    await bus.publish(str(trip_id), "done", {})
