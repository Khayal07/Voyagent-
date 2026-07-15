from fastapi import APIRouter, HTTPException, Query

from ..services.rates import SUPPORTED, get_rates

router = APIRouter(prefix="/api/rates", tags=["rates"])


# Auth yoxdur — ictimai məzənnə datası, paylaşma görünüşü də istifadə edir
@router.get("")
async def rates(base: str = Query("USD")):
    base = base.upper()
    if base not in SUPPORTED:
        raise HTTPException(status_code=422, detail=f"base bunlardan biri olmalıdır: {', '.join(SUPPORTED)}")
    result = await get_rates(base)
    if result is None:
        raise HTTPException(status_code=503, detail="Məzənnə servisi əlçatmazdır")
    return {"base": base, "rates": result}
