import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import models  # noqa: F401 — create_all üçün modellər qeydiyyata düşməlidir
from .db import engine, init_db
from .llm.client import LLMError, call_llm
from .routers.trips import router as trips_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("voyagent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database tables ready")
    yield


app = FastAPI(title="Voyagent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips_router)


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/debug/llm")
async def debug_llm():
    """LLM provider zəncirini yoxlamaq üçün minimal çağırış."""
    try:
        result = await call_llm(
            [{"role": "user", "content": 'Cavab yalnız bu JSON olsun: {"ok": true}'}],
            max_tokens=20,
            temperature=0,
        )
    except (LLMError, Exception) as e:
        raise HTTPException(status_code=502, detail=f"Hər iki provider uğursuz: {e}")
    return {
        "content": result.content,
        "provider": result.provider,
        "model": result.model,
        "fallback_reason": result.fallback_reason,
    }
