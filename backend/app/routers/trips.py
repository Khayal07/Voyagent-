import asyncio
import json
import secrets
import uuid
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..agents import planner
from ..auth import get_current_user
from ..db import get_session
from ..events import bus
from ..models import AgentMessage, Trip, User
from ..orchestrator import run_trip_planning
from ..ratelimit import limit_share, trip_limiter
from ..schemas import ItineraryOut, ItineraryUpdate, ShareOut, TripCreate, TripDetail, TripOut

router = APIRouter(prefix="/api/trips", tags=["trips"])

# Fire-and-forget task-lar GC ilə yarımçıq öldürülməsin deyə güclü referans saxlanılır
_background_tasks: set[asyncio.Task] = set()


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
    task = asyncio.create_task(run_trip_planning(trip.id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
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


# QEYD: /{trip_id}-dən ƏVVƏL elan olunmalıdır ("shared" UUID kimi parse olunmasın)
@router.get("/shared/{token}", response_model=TripDetail)
async def get_shared_trip(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Oxu-yalnız public görünüş — auth tələb etmir, yalnız token bilənlər açır."""
    limit_share(request)  # public endpoint — token enumerasiyasına qarşı IP limiti
    result = await session.execute(
        select(Trip)
        .options(selectinload(Trip.messages), selectinload(Trip.itinerary))
        .where(Trip.share_token == token)
    )
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(status_code=404, detail="Paylaşma linki etibarsızdır")
    return trip


@router.post("/{trip_id}/share", response_model=ShareOut)
async def share_trip(
    trip_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Sahib üçün paylaşma tokeni yaradır (idempotent — mövcuddursa eynisini qaytarır)."""
    result = await session.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalar_one_or_none()
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status_code=404, detail="Trip tapılmadı")
    if not trip.share_token:
        # Toqquşma astronomik dərəcədə az ehtimallıdır, amma yenə də təkrar cəhd edilir
        for _ in range(3):
            trip.share_token = secrets.token_urlsafe(12)
            try:
                await session.commit()
                break
            except IntegrityError:
                await session.rollback()
                await session.refresh(trip)
        else:
            raise HTTPException(status_code=500, detail="Paylaşma tokeni yaradıla bilmədi")
    return ShareOut(token=trip.share_token)


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


@router.patch("/{trip_id}/itinerary", response_model=ItineraryOut)
async def update_itinerary(
    trip_id: uuid.UUID,
    data: ItineraryUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Drag&drop redaktəsi: yalnız mövcud item-ların yenidən düzülməsi/silinməsi.

    Cədvəl deterministik yenidən qurulur (planner) — LLM çağırışı yoxdur.
    """
    result = await session.execute(
        select(Trip).options(selectinload(Trip.itinerary)).where(Trip.id == trip_id)
    )
    trip = result.scalar_one_or_none()
    if trip is None or trip.user_id != user.id or trip.itinerary is None:
        raise HTTPException(status_code=404, detail="Trip tapılmadı")
    if trip.status != "done":
        raise HTTPException(status_code=409, detail="Plan hələ hazır deyil")

    itinerary = trip.itinerary
    stored_days = {d["day"]: d for d in itinerary.days}

    if {d.day for d in data.days} != set(stored_days):
        raise HTTPException(status_code=422, detail="Gün dəsti mövcud planla üst-üstə düşmür")

    # Yalnız planda artıq olan item-lar qəbul edilir — kənardan item inject etmək mümkün deyil.
    # Eyni yer birdən çox gündə ola bilər, ona görə ad başına icazəli say (Counter) izlənir;
    # bu, günlər arası daşımağa da imkan verir, saxta təkrarı isə bloklayır.
    pool: dict[str, dict] = {}
    available: Counter = Counter()
    for d in itinerary.days:
        for i in d["items"]:
            key = i["name"].casefold()
            pool[key] = i
            available[key] += 1

    used: Counter = Counter()
    new_days, weather = [], []
    for d in sorted(data.days, key=lambda x: x.day):
        items = []
        for name in d.items:
            key = name.casefold()
            if key not in pool:
                raise HTTPException(status_code=422, detail=f"Naməlum yer: {name}")
            used[key] += 1
            if used[key] > available[key]:
                raise HTTPException(status_code=422, detail=f"Təkrarlanan yer: {name}")
            items.append(pool[key])
        new_days.append({"day": d.day, "items": items})
        weather.append(stored_days[d.day].get("weather"))
    if not used:
        raise HTTPException(status_code=422, detail="Ən azı bir yer qalmalıdır")

    schedule, total_cost = planner.build_schedule(trip, new_days, weather=weather, lodging=itinerary.lodging)
    itinerary.days = schedule
    itinerary.total_cost = total_cost
    await session.commit()
    await session.refresh(itinerary)
    return itinerary


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
