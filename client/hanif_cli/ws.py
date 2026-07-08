"""WebSocket connection to a channel room with auto-reconnect."""
from __future__ import annotations

import asyncio
import json
from typing import Awaitable, Callable

import websockets

from .config import Session

EventHandler = Callable[[dict], Awaitable[None]]


class ChatSocket:
    """Manage a single channel WebSocket connection.

    `on_event` is awaited for every server event; `on_status` is called with
    a human-readable connection state ("connected", "reconnecting", ...).
    """

    def __init__(
        self,
        session: Session,
        channel_slug: str,
        on_event: EventHandler,
        on_status: Callable[[str], None] | None = None,
    ):
        self.session = session
        self.channel_slug = channel_slug
        self.on_event = on_event
        self.on_status = on_status or (lambda s: None)
        self._ws = None
        self._task: asyncio.Task | None = None
        self._closed = False

    @property
    def url(self) -> str:
        return f"{self.session.ws_url}/ws/chat/{self.channel_slug}/?token={self.session.access}"

    def start(self) -> None:
        self._closed = False
        self._task = asyncio.create_task(self._run())

    async def close(self) -> None:
        self._closed = True
        if self._ws is not None:
            await self._ws.close()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass

    async def send(self, payload: dict) -> None:
        if self._ws is not None:
            await self._ws.send(json.dumps(payload))

    async def send_message(self, content: str) -> None:
        await self.send({"type": "message", "content": content})

    async def send_typing(self) -> None:
        await self.send({"type": "typing"})

    async def edit(self, message_id: int, content: str) -> None:
        await self.send({"type": "edit", "id": message_id, "content": content})

    async def delete(self, message_id: int) -> None:
        await self.send({"type": "delete", "id": message_id})

    async def _run(self) -> None:
        backoff = 1
        while not self._closed:
            try:
                async with websockets.connect(self.url) as ws:
                    self._ws = ws
                    backoff = 1
                    self.on_status("connected")
                    async for raw in ws:
                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        await self.on_event(event)
            except asyncio.CancelledError:
                raise
            except Exception:
                self._ws = None
                if self._closed:
                    break
                self.on_status("reconnecting")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 15)
        self._ws = None
        self.on_status("disconnected")
