"""Postgres-dayaqlı açar-dəyər cache: in-memory L1 + DB L2 — restartlarda itmir.

DB əlçatmaz olsa səssizcə yalnız yaddaşla işləyir (servis funksiyaları pozulmur).
"""

import logging
from typing import Any

logger = logging.getLogger("voyagent.cache")

# "cache-də yoxdur" ilə "cache-də None var" fərqi üçün sentinel
MISS = object()


# L1 yaddaş cache-i limitsiz böyüməsin deyə sadə FIFO tavanı
MEM_MAX = 2000


class KVCache:
    def __init__(self, namespace: str, persist: bool = True):
        self.ns = namespace
        self.persist = persist
        self._mem: dict[str, Any] = {}

    def _k(self, key: str) -> str:
        return f"{self.ns}:{key}"[:255]

    def _remember(self, k: str, value: Any) -> None:
        if k not in self._mem and len(self._mem) >= MEM_MAX:
            self._mem.pop(next(iter(self._mem)))  # ən köhnə girişi at
        self._mem[k] = value

    async def get(self, key: str) -> Any:
        k = self._k(key)
        if k in self._mem:
            return self._mem[k]
        if not self.persist:
            return MISS
        try:
            from ..db import SessionLocal
            from ..models import CacheEntry

            async with SessionLocal() as s:
                row = await s.get(CacheEntry, k)
        except Exception as e:
            logger.warning("Cache oxuna bilmədi (%s): %s", k, e)
            return MISS
        if row is None:
            return MISS
        self._remember(k, row.value)
        return row.value

    async def set(self, key: str, value: Any) -> None:
        k = self._k(key)
        self._remember(k, value)
        if not self.persist:
            return
        try:
            from ..db import SessionLocal
            from ..models import CacheEntry

            async with SessionLocal() as s:
                await s.merge(CacheEntry(key=k, value=value))
                await s.commit()
        except Exception as e:
            logger.warning("Cache yazıla bilmədi (%s): %s", k, e)
