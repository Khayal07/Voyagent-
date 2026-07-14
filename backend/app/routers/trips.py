import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import get_current_user
from ..db import get_session
from ..events import bus
from ..models import AgentMessage, Trip, User
from ..orchestrator import run_trip_planning
from ..ratelimit import trip_limiter
from ..schemas import TripCreate, TripDetail, TripOut

router = APIRouter(prefix="/api/trips", tags=["trips"])


def sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


@router.post("", response_model=TripOut, status_code=201)
async def create_trip(
    data: TripCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    # LLM xərcini qorumaq üçün istifadəçi başına limit
    trip_limiter.check(str(user.id))
    trip = Trip(**data.model_dump(), user_id=user.id)
    session.add(trip)
    await session.commit()
    await session.refresh(trip)
    asyncio.create_task(run_trip_planning(trip.id))
    return trip


@router.get("", response_model=list[TripOut])
async def list_trips(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Trip).where(Trip.user_id == user.id).order_by(Trip.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(
    trip_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Trip)
        .options(selectinload(Trip.messages), selectinload(Trip.itinerary))
        .where(Trip.id == trip_id)
    )
    trip = result.scalar_one_or_none()
    # özgə trip-də 404 — mövcudluq məlumatı sızmasın
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status_code=404, detail="Trip tapılmadı")
    return trip


@router.get("/{trip_id}/stream")
async def stream_trip(
    trip_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    trip = await session.get(Trip, trip_id)
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status_code=404, detail="Trip tapılmadı")
    initial_status = trip.status

    # Subscribe olmamışdan əvvəl göndərilən mesajlar itməsin deyə mövcud mesajlar replay olunur;
    # subscribe → DB oxu ardıcıllığı sayəsində boşluq qalmır, dublikatlar id ilə süzülür.
    queue = bus.subscribe(str(trip_id))
    result = await session.execute(
        select(AgentMessage).where(AgentMessage.trip_id == trip_id).order_by(AgentMessage.id)
    )
    existing = result.scalars().all()

    async def generator():
        last_id = 0
        try:
            yield sse("status", {"status": initial_status})
            for m in existing:
                last_id = m.id
                yield sse(
                    "agent_message",
                    {"id": m.id, "agent": m.agent, "round": m.round, "role": m.role,
                     "content": m.content, "payload": m.payload},
                )
            if initial_status in ("done", "failed"):
                yield sse("done", {})
                return
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event["type"] == "agent_message" and event["data"].get("id", 0) <= last_id:
                    continue
                yield sse(event["type"], event["data"])
                if event["type"] in ("done", "error"):
                    break
        finally:
            bus.unsubscribe(str(trip_id), queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
