"""Regression test: an idle WebSocket must survive past the 5s bzpopmin block
without the channel layer raising redis TimeoutError and dropping the socket.
"""
import asyncio
import json
import sys

import httpx
import websockets

API = "http://127.0.0.1:8000/api"
WS = "ws://127.0.0.1:8000/ws/chat"
SUF = "idle"
U = {"username": f"idle_{SUF}", "email": f"idle_{SUF}@t.io", "password": "s3cretpwd!"}


async def main() -> int:
    with httpx.Client(timeout=10) as c:
        c.post(f"{API}/auth/register", json=U)
        tok = c.post(f"{API}/auth/login", json={"username": U["username"], "password": U["password"]}).json()["access"]
        h = {"Authorization": f"Bearer {tok}"}
        ch = c.post(f"{API}/channels", headers=h, json={"name": f"idle-{SUF}"}).json()
        slug = ch["name"]

    async with websockets.connect(f"{WS}/{slug}/?token={tok}") as ws:
        # drain join
        try:
            while True:
                await asyncio.wait_for(ws.recv(), timeout=0.3)
        except asyncio.TimeoutError:
            pass

        print("WS ouvert — inactivité 8s (dépasse le blocage bzpopmin de 5s)…")
        await asyncio.sleep(8)

        # If the channel layer had raised, the server would have closed us.
        assert ws.state.name == "OPEN", f"WS fermé pendant l'inactivité: {ws.state.name}"
        print("[PASS] WS toujours ouvert après 8s d'inactivité")

        # And it must still deliver messages.
        await ws.send(json.dumps({"type": "message", "content": "encore vivant"}))
        got = None
        try:
            while True:
                ev = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
                if ev.get("type") == "message":
                    got = ev
                    break
        except asyncio.TimeoutError:
            pass
        assert got and got["content"] == "encore vivant", f"pas de message reçu: {got}"
        print("[PASS] Message toujours délivré après inactivité")

    print("\nRÉSULTAT: OK — plus de drop lié au TimeoutError Redis")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
