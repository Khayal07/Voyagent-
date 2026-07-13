"""Test infrastrukturu: in-memory SQLite + FastAPI dependency override.

Real LLM/HTTP çağırışı YOXDUR — hər şey mock-lanır.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base, get_session
from app.main import app


@pytest.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest.fixture
async def client(engine, monkeypatch):
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session():
        async with maker() as s:
            yield s

    async def noop_planning(trip_id):
        return None

    # create_trip real pipeline-i işə salmasın
    from app.routers import trips as trips_module

    monkeypatch.setattr(trips_module, "run_trip_planning", noop_planning)

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def make_item(name="Colosseum", category="history", est_cost=20.0, duration_min=90, lat=None, lon=None, **kw):
    return {
        "name": name,
        "category": category,
        "est_cost": est_cost,
        "duration_min": duration_min,
        "lat": lat,
        "lon": lon,
        "llm_lat": kw.get("llm_lat"),
        "llm_lon": kw.get("llm_lon"),
    }
