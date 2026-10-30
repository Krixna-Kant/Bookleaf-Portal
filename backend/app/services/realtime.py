from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from app.enums import UserRole


class EventHub:
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[dict]] = []

    def subscribe(self) -> asyncio.Queue[dict]:
        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict]) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def publish(self, event: dict) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                continue


hub = EventHub()


def publish_ticket_event(event_type: str, ticket_id: int, author_id: int) -> None:
    hub.publish({"type": event_type, "ticket_id": ticket_id, "author_id": author_id})


def event_visible_to(event: dict, user_id: int, role: UserRole) -> bool:
    if role == UserRole.ADMIN:
        return True
    return event.get("author_id") == user_id


async def event_stream(user_id: int, role: UserRole) -> AsyncIterator[str]:
    queue = hub.subscribe()
    try:
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=20)
            except TimeoutError:
                yield "data: {\"type\":\"ping\"}\n\n"
                continue
            if event_visible_to(event, user_id, role):
                yield f"data: {json.dumps(event)}\n\n"
    finally:
        hub.unsubscribe(queue)
