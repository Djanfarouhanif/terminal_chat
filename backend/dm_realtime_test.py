"""Test du temps réel des messages privés (DM) — bidirectionnel."""
import asyncio
import json
import sys

import httpx
import websockets

API = "http://127.0.0.1:8000/api"
WS = "ws://127.0.0.1:8000/ws/dm/"
S = "dmrt"
ALICE = {"username": f"alice_{S}", "email": f"a_{S}@t.io", "password": "s3cretpwd!"}
BOB = {"username": f"bob_{S}", "email": f"b_{S}@t.io", "password": "s3cretpwd!"}


def login(c, u):
    c.post(f"{API}/auth/register", json=u)
    r = c.post(f"{API}/auth/login", json={"username": u["username"], "password": u["password"]})
    return r.json()["access"]


async def drain(ws, timeout=2.0):
    out = []
    try:
        while True:
            out.append(json.loads(await asyncio.wait_for(ws.recv(), timeout)))
    except asyncio.TimeoutError:
        pass
    return out


async def main() -> int:
    with httpx.Client(timeout=10) as c:
        atok = login(c, ALICE)
        btok = login(c, BOB)

    results = []
    def check(n, ok): results.append((n, ok)); print(f"[{'PASS' if ok else 'FAIL'}] {n}")

    async with websockets.connect(f"{WS}?token={atok}") as wa, \
               websockets.connect(f"{WS}?token={btok}") as wb:
        await asyncio.sleep(0.4)
        # Alice envoie un MP à Bob via REST
        with httpx.Client(timeout=10) as c:
            c.post(f"{API}/dm", headers={"Authorization": f"Bearer {atok}"},
                   json={"receiver": BOB["username"], "content": "MP temps réel"})
        b_events = await drain(wb)
        a_events = await drain(wa)
        got_bob = any(e.get("type") == "dm_message" and e.get("content") == "MP temps réel"
                      and e.get("sender") == ALICE["username"] for e in b_events)
        got_alice_echo = any(e.get("type") == "dm_message" and e.get("content") == "MP temps réel"
                             for e in a_events)
        check("Bob reçoit le MP en direct", got_bob)
        check("Alice reçoit l'écho de son MP", got_alice_echo)

        # Bob répond → Alice reçoit en direct
        with httpx.Client(timeout=10) as c:
            c.post(f"{API}/dm", headers={"Authorization": f"Bearer {btok}"},
                   json={"receiver": ALICE["username"], "content": "bien reçu"})
        a_events2 = await drain(wa)
        check("Alice reçoit la réponse de Bob en direct",
              any(e.get("content") == "bien reçu" and e.get("sender") == BOB["username"] for e in a_events2))

    passed = sum(1 for _, ok in results if ok)
    print(f"\nRÉSULTAT: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
