import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import models  # noqa: F401 — metadata qeydiyyatı üçün
from .config import DEFAULT_JWT_SECRET, settings
from .db import engine, run_migrations
from .llm.client import call_llm
from .routers.auth import router as auth_router
from .routers.rates import router as rates_router
from .routers.trips import router as trips_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("voyagent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Prod-da default JWT sirri ilə start-a icazə vermə (token saxtalaşdırma riski)
    if not settings.debug_endpoints and settings.jwt_secret == DEFAULT_JWT_SECRET:
        raise RuntimeError("JWT_SECRET production üçün dəyişdirilməlidir")
    await run_migrations()
    logger.info("Database migrations applied")
    yield


app = FastAPI(title="Voyagent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(rates_router)
app.include_router(trips_router)


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/debug/llm")
async def debug_llm():
    """LLM provider zəncirini yoxlamaq üçün minimal çağırış (yalnız debug rejimində)."""
    if not settings.debug_endpoints:
        raise HTTPException(status_code=404, detail="Not Found")
    try:
        result = await call_llm(
            [{"role": "user", "content": 'Cavab yalnız bu JSON olsun: {"ok": true}'}],
            max_tokens=20,
            temperature=0,
        )
    except Exception:
        # Xəta detalı log-a yazılır, provider məlumatı client-ə sızmasın
        logger.exception("debug_llm uğursuz")
        raise HTTPException(status_code=502, detail="Hər iki provider uğursuz")
    return {
        "content": result.content,
        "provider": result.provider,
        "model": result.model,
        "fallback_reason": result.fallback_reason,
    }
