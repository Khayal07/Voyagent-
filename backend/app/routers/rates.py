from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ..services.rates import SUPPORTED, get_rates

router = APIRouter(prefix="/api/rates", tags=["rates"])


@router.get("", dependencies=[Depends(get_current_user)])
async def rates(base: str = Query("USD")):
    base = base.upper()
    if base not in SUPPORTED:
        raise HTTPException(status_code=422, detail=f"base bunlardan biri olmalıdır: {', '.join(SUPPORTED)}")
    result = await get_rates(base)
    if result is None:
        raise HTTPException(status_code=503, detail="Məzənnə servisi əlçatmazdır")
    return {"base": base, "rates": result}
