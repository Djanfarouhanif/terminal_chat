"""End-to-end smoke test for the Relay backend (REST + WebSocket)."""
import asyncio
import json
import sys

import httpx
import websockets

API = "http://127.0.0.1:8000/api"
WS = "ws://127.0.0.1:8000/ws/chat"

# unique suffix so the test is re-runnable without wiping the DB
SUF = str(abs(hash(sys.argv[0])) % 100000)
ALICE = {"username": f"alice_{SUF}", "email": f"alice_{SUF}@t.io", "password": "s3cretpwd!"}
BOB = {"username": f"bob_{SUF}", "email": f"bob_{SUF}@t.io", "password": "s3cretpwd!"}


def register_and_login(client, user):
    r = client.post(f"{API}/auth/register", json=user)
    assert r.status_code in (201, 400), f"register {user['username']}: {r.status_code} {r.text}"
    r = client.post(f"{API}/auth/login", json={"username": user["username"], "password": user["password"]})
    assert r.status_code == 200, f"login: {r.status_code} {r.text}"
    data = r.json()
    assert "access" in data and "user" in data, data
    return data["access"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def main():
    results = []

    def check(name, cond):
        results.append((name, cond))
        print(f"[{'PASS' if cond else 'FAIL'}] {name}")

    with httpx.Client(timeout=10) as c:
        # --- Auth ---
        alice_tok = register_and_login(c, ALICE)
        bob_tok = register_and_login(c, BOB)
        check("register + login (JWT)", bool(alice_tok and bob_tok))

        # --- Profile ---
        r = c.get(f"{API}/profile", headers=auth(alice_tok))
        check("GET /profile", r.status_code == 200 and r.json()["username"] == ALICE["username"])

        r = c.patch(f"{API}/profile", headers=auth(alice_tok), json={"status": "busy"})
        check("PATCH /profile status", r.status_code == 200 and r.json()["status"] == "busy")

        # --- Users list ---
        r = c.get(f"{API}/users", headers=auth(alice_tok))
        check("GET /users", r.status_code == 200 and r.json()["count"] >= 2)

        # --- Channels ---
        r = c.post(f"{API}/channels", headers=auth(alice_tok), json={"name": f"general-{SUF}", "description": "Salon de test"})
        check("POST /channels (create)", r.status_code == 201)
        chan_id = r.json()["id"]
        chan_slug = r.json()["name"]

        r = c.post(f"{API}/channels/{chan_id}/join", headers=auth(bob_tok))
        check("POST /channels/{id}/join (bob)", r.status_code == 200 and r.json()["member_count"] == 2)

        r = c.get(f"{API}/channels", headers=auth(bob_tok))
        check("GET /channels list", r.status_code == 200 and any(ch["id"] == chan_id for ch in r.json()["results"]))

        # --- REST message ---
        r = c.post(f"{API}/messages", headers=auth(alice_tok), json={"channel": chan_id, "content": "Message REST"})
        check("POST /messages (REST)", r.status_code == 201)
        msg_id = r.json()["id"]

        r = c.patch(f"{API}/messages/{msg_id}", headers=auth(alice_tok), json={"content": "Message REST édité"})
        check("PATCH /messages/{id} (edit)", r.status_code == 200 and r.json()["edited"] is True)

        # --- DM ---
        r = c.post(f"{API}/dm", headers=auth(alice_tok), json={"receiver": BOB["username"], "content": "Salut Bob"})
        check("POST /dm", r.status_code == 201)
        r = c.get(f"{API}/dm?user={BOB['username']}", headers=auth(alice_tok))
        check("GET /dm history", r.status_code == 200 and r.json()["count"] >= 1)

        # --- Search ---
        r = c.get(f"{API}/search?q=general-{SUF}", headers=auth(alice_tok))
        check("GET /search", r.status_code == 200 and len(r.json()["channels"]) >= 1)

    # --- WebSocket real-time between two clients ---
    ws_ok = False
    edit_ok = False
    try:
        async with websockets.connect(f"{WS}/{chan_slug}/?token={alice_tok}") as wa, \
                   websockets.connect(f"{WS}/{chan_slug}/?token={bob_tok}") as wb:
            # drain join events
            await asyncio.sleep(0.4)
            async def drain(ws):
                out = []
                try:
                    while True:
                        out.append(json.loads(await asyncio.wait_for(ws.recv(), timeout=0.3)))
                except asyncio.TimeoutError:
                    pass
                return out
            await drain(wa); await drain(wb)

            # alice sends a live message -> bob should receive it
            await wa.send(json.dumps({"type": "message", "content": "Hello temps réel"}))
            bob_events = await drain(wb)
            msg_events = [e for e in bob_events if e.get("type") == "message"]
            ws_ok = any(e["content"] == "Hello temps réel" and e["sender"] == ALICE["username"] for e in msg_events)
            new_msg_id = msg_events[0]["id"] if msg_events else None

            # alice edits it -> bob should see edit
            if new_msg_id:
                await wa.send(json.dumps({"type": "edit", "id": new_msg_id, "content": "Édité en direct"}))
                bob_edit = await drain(wb)
                edit_ok = any(e.get("type") == "edit" and e.get("content") == "Édité en direct" for e in bob_edit)
    except Exception as exc:
        print(f"WS error: {exc}")

    check("WS realtime message broadcast", ws_ok)
    check("WS realtime edit broadcast", edit_ok)

    print("\n" + "=" * 40)
    passed = sum(1 for _, c in results if c)
    print(f"RÉSULTAT: {passed}/{len(results)} tests réussis")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
