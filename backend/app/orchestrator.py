"""Negotiation orchestrator: agentləri ardıcıl işə salır, mesajları DB-yə yazır və SSE-yə ötürür."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .agents import budget, interest, logistics, planner
from .db import SessionLocal
from .events import bus
from .llm.client import LLMResult
from .models import AgentMessage, Itinerary, Trip
from .services.geocode import geocode

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
    session: AsyncSession, trip_id: uuid.UUID, agent: str, round_: int, llm: LLMResult | None
) -> None:
    """Provider fallback baş veribsə bunu şəffaf şəkildə istifadəçiyə göstərir."""
    if llm is not None and llm.fallback_reason:
        await emit(
            session, trip_id, "system", round_, "info",
            f"{agent.capitalize()} Agent OpenRouter fallback modelinə keçdi ({llm.model}). "
            f"Səbəb: {llm.fallback_reason[:150]}",
        )


async def set_status(session: AsyncSession, trip: Trip, status: str) -> None:
    trip.status = status
    await session.commit()
    await bus.publish(str(trip.id), "status", {"status": status})


async def _geocode_days(days: list[dict], city: str) -> None:
    for d in days:
        for item in d["items"]:
            if item.get("lat") is None:
                coords = await geocode(item["name"], city)
                if coords:
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
            await emit(session, trip_id, "system", 0, "info", f"Planlaşdırma dayandı: {str(e)[:200]}")
            await set_status(session, trip, "failed")
            await bus.publish(str(trip_id), "error", {"detail": str(e)[:200]})


async def _run(session: AsyncSession, trip: Trip) -> None:
    trip_id = trip.id
    num_days = (trip.end_date - trip.start_date).days + 1
    await set_status(session, trip, "planning")
    await emit(
        session, trip_id, "system", 0, "info",
        f"{trip.city} üçün {num_days} günlük plan hazırlanır — 4 agent işə başlayır.",
    )

    # Raund 0: Interest Agent ilkin təklif
    say, days, llm = await interest.propose(trip, num_days)
    await note_fallback(session, trip_id, "interest", 0, llm)
    await emit(session, trip_id, "interest", 0, "proposal", say, {"days": days})

    await emit(session, trip_id, "system", 0, "info", "Yerlərin koordinatları tapılır (OpenStreetMap)...")
    await _geocode_days(days, trip.city)

    # Negotiation dövrəsi
    for round_no in range(1, MAX_ROUNDS + 2):
        budget_ok, total, budget_objs = budget.check(trip, days)
        if budget_ok:
            await emit(session, trip_id, "budget", round_no, "approval", budget.approval_message(trip, total))
        else:
            msg, b_llm = await budget.objection_message(trip, total, budget_objs)
            await note_fallback(session, trip_id, "budget", round_no, b_llm)
            await emit(session, trip_id, "budget", round_no, "objection", msg, {"objections": budget_objs, "total": total})

        logistics_ok, stats, logistics_objs = logistics.check(days)
        if logistics_ok:
            await emit(session, trip_id, "logistics", round_no, "approval", logistics.approval_message(stats))
        else:
            msg, l_llm = await logistics.objection_message(trip.city, logistics_objs)
            await note_fallback(session, trip_id, "logistics", round_no, l_llm)
            await emit(session, trip_id, "logistics", round_no, "objection", msg, {"objections": logistics_objs})

        objections = budget_objs + logistics_objs
        if not objections:
            break
        if round_no > MAX_ROUNDS:
            await emit(
                session, trip_id, "system", round_no, "info",
                "Maksimum danışıq raundu keçildi — mövcud ən yaxşı variantla davam edilir.",
            )
            break

        say, days, llm = await interest.revise(trip, days, objections)
        await note_fallback(session, trip_id, "interest", round_no, llm)
        await emit(session, trip_id, "interest", round_no, "revision", say, {"days": days})
        await _geocode_days(days, trip.city)

    # Planner: yekun cədvəl
    schedule, total_cost = planner.build_schedule(trip, days)
    say, p_llm = await planner.summary_message(trip, schedule, total_cost)
    await note_fallback(session, trip_id, "planner", 99, p_llm)
    await emit(session, trip_id, "planner", 99, "final", say, {"days": schedule, "total_cost": total_cost})

    session.add(Itinerary(trip_id=trip_id, days=schedule, total_cost=total_cost))
    await session.commit()
    await bus.publish(str(trip_id), "itinerary", {"days": schedule, "total_cost": total_cost})

    await set_status(session, trip, "done")
    await bus.publish(str(trip_id), "done", {})
