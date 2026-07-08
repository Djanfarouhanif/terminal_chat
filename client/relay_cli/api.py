"""Async REST client for the Relay backend (httpx), with JWT refresh."""
from __future__ import annotations

import httpx

from .config import Session


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"{status}: {detail}")


class ApiClient:
    def __init__(self, session: Session):
        self.session = session
        self._client = httpx.AsyncClient(base_url=session.api_url, timeout=10)

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- low level -----------------------------------------------------

    def _auth_headers(self) -> dict:
        if self.session.access:
            return {"Authorization": f"Bearer {self.session.access}"}
        return {}

    async def _request(self, method: str, path: str, *, auth: bool = True, **kwargs):
        headers = kwargs.pop("headers", {})
        if auth:
            headers.update(self._auth_headers())
        resp = await self._client.request(method, path, headers=headers, **kwargs)

        if resp.status_code == 401 and auth and self.session.refresh:
            if await self._refresh():
                headers.update(self._auth_headers())
                resp = await self._client.request(method, path, headers=headers, **kwargs)

        if resp.status_code >= 400:
            detail = resp.text
            try:
                body = resp.json()
                detail = body.get("detail") or _first_error(body) or detail
            except Exception:
                pass
            raise ApiError(resp.status_code, detail)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    async def _refresh(self) -> bool:
        try:
            resp = await self._client.post(
                "/api/auth/refresh", json={"refresh": self.session.refresh}
            )
        except httpx.HTTPError:
            return False
        if resp.status_code == 200:
            data = resp.json()
            self.session.access = data["access"]
            if "refresh" in data:
                self.session.refresh = data["refresh"]
            self.session.save()
            return True
        return False

    # --- auth ----------------------------------------------------------

    async def register(self, username: str, email: str, password: str):
        return await self._request(
            "POST",
            "/api/auth/register",
            auth=False,
            json={"username": username, "email": email, "password": password},
        )

    async def login(self, username: str, password: str):
        data = await self._request(
            "POST",
            "/api/auth/login",
            auth=False,
            json={"username": username, "password": password},
        )
        self.session.access = data["access"]
        self.session.refresh = data["refresh"]
        self.session.username = data["user"]["username"]
        self.session.save()
        return data

    async def logout(self):
        try:
            await self._request("POST", "/api/auth/logout")
        finally:
            self.session.clear()

    # --- resources -----------------------------------------------------

    async def profile(self):
        return await self._request("GET", "/api/profile")

    async def update_profile(self, **fields):
        return await self._request("PATCH", "/api/profile", json=fields)

    async def users(self, online: bool = False, search: str = ""):
        params = {}
        if online:
            params["online"] = "1"
        if search:
            params["search"] = search
        return await self._request("GET", "/api/users", params=params)

    async def channels(self):
        return await self._request("GET", "/api/channels")

    async def create_channel(self, name: str, description: str = ""):
        return await self._request(
            "POST", "/api/channels", json={"name": name, "description": description}
        )

    async def join_channel(self, channel_id: int):
        return await self._request("POST", f"/api/channels/{channel_id}/join")

    async def leave_channel(self, channel_id: int):
        return await self._request("POST", f"/api/channels/{channel_id}/leave")

    async def messages(self, channel_id: int):
        return await self._request(
            "GET", "/api/messages", params={"channel": channel_id}
        )

    async def dm_history(self, username: str):
        return await self._request("GET", "/api/dm", params={"user": username})

    async def send_dm(self, receiver: str, content: str):
        return await self._request(
            "POST", "/api/dm", json={"receiver": receiver, "content": content}
        )

    async def search(self, query: str):
        return await self._request("GET", "/api/search", params={"q": query})

    async def client_version(self):
        return await self._request("GET", "/api/client-version", auth=False)


def _first_error(body) -> str:
    """Extract the first human-readable message from a DRF error body."""
    if isinstance(body, dict):
        for value in body.values():
            if isinstance(value, list) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    return ""
