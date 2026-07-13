"""Trip-lərə görə in-memory event bus: orchestrator publish edir, SSE endpoint subscribe olur."""

import asyncio
from collections import defaultdict


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, trip_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[trip_id].append(q)
        return q

    def unsubscribe(self, trip_id: str, q: asyncio.Queue) -> None:
        subs = self._subscribers.get(trip_id, [])
        if q in subs:
            subs.remove(q)
        if not subs:
            self._subscribers.pop(trip_id, None)

    async def publish(self, trip_id: str, event_type: str, data: dict) -> None:
        for q in list(self._subscribers.get(trip_id, [])):
            await q.put({"type": event_type, "data": data})


bus = EventBus()
