import asyncio
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with SessionLocal() as session:
        yield session


def _alembic_config():
    from alembic.config import Config

    return Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))


async def run_migrations() -> None:
    """Alembic upgrade head; create_all dövründən qalan DB-ni əvvəlcə 0001 kimi stamp edir."""
    from alembic import command

    def _tables(conn):
        insp = inspect(conn)
        return insp.has_table("trips"), insp.has_table("alembic_version")

    async with engine.connect() as conn:
        has_schema, has_version = await conn.run_sync(_tables)

    cfg = _alembic_config()
    if has_schema and not has_version:
        await asyncio.to_thread(command.stamp, cfg, "0001")
    await asyncio.to_thread(command.upgrade, cfg, "head")
