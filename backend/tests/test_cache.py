"""KVCache: in-memory L1 + DB L2 davranışı (SQLite ilə)."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

import app.db as db_module
from app.services.cache import MISS, KVCache


@pytest.fixture
def use_test_db(engine, monkeypatch):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db_module, "SessionLocal", maker)


async def test_value_survives_new_instance(use_test_db):
    c1 = KVCache("t")
    await c1.set("k", {"a": 1})
    # yeni instans = boş L1 yaddaş → DB-dən oxumalıdır (restart simulyasiyası)
    c2 = KVCache("t")
    assert await c2.get("k") == {"a": 1}


async def test_miss_vs_stored_none(use_test_db):
    c = KVCache("t")
    assert await c.get("unknown") is MISS
    await c.set("nf", None)
    assert (await KVCache("t").get("nf")) is None


async def test_no_persist_skips_db(use_test_db):
    c1 = KVCache("t", persist=False)
    await c1.set("k", [1, 2])
    assert await c1.get("k") == [1, 2]
    assert await KVCache("t").get("k") is MISS


async def test_db_failure_degrades_gracefully(monkeypatch):
    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(db_module, "SessionLocal", boom)
    c = KVCache("t")
    assert await c.get("k") is MISS
    await c.set("k", 1)  # exception atmamalıdır
    assert await c.get("k") == 1  # L1-dən gəlir