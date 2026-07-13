"""Negotiation orchestrator: agentləri ardıcıl işə salır, mesajları DB-yə yazır və SSE-yə ötürür."""

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .db import SessionLocal
from .events import bus
from .models import AgentMessage, Trip

logger = logging.getLogger("voyagent.orchestrator")


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


async def set_status(session: AsyncSession, trip: Trip, status: str) -> None:
    trip.status = status
    await session.commit()
    await bus.publish(str(trip.id), "status", {"status": status})


async def run_trip_planning(trip_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        trip = await session.get(Trip, trip_id)
        if trip is None:
            logger.error("Trip tapılmadı: %s", trip_id)
            return
        try:
            await set_status(session, trip, "planning")
            # TODO (Mərhələ 4): real agent negotiation dövrəsi
            await emit(session, trip_id, "system", 0, "info", "Agentlər hazırlanır — negotiation tezliklə əlavə olunacaq.")
            await asyncio.sleep(1)
            await set_status(session, trip, "done")
            await bus.publish(str(trip_id), "done", {})
        except Exception as e:
            logger.exception("Planlaşdırma xətası (trip=%s)", trip_id)
            await set_status(session, trip, "failed")
            await bus.publish(str(trip_id), "error", {"detail": str(e)})
