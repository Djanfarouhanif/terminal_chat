"""Render a screenshot of the hacker REPL to an SVG for visual review."""
import asyncio
import os
import tempfile

os.environ["RELAY_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hanif_snap_")
os.environ["RELAY_API"] = "http://127.0.0.1:8000"

import httpx  # noqa: E402
from relay_cli.app import ChatApp  # noqa: E402
from relay_cli.config import Session  # noqa: E402
from textual.widgets import Input  # noqa: E402

SUF = str(os.getpid())
U = {"username": f"h4x0r_{SUF}", "email": f"h_{SUF}@t.io", "password": "s3cretpwd!"}


def preauth():
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as c:
        c.post("/api/auth/register", json=U)
        r = c.post("/api/auth/login", json={"username": U["username"], "password": U["password"]})
        d = r.json()
    s = Session.load()
    s.access, s.refresh, s.username = d["access"], d["refresh"], d["user"]["username"]
    s.save()


async def cmd(app, pilot, line, wait=1.2):
    app.query_one("#prompt", Input).value = line
    await pilot.press("enter")
    await asyncio.sleep(wait)
    await pilot.pause()


async def main():
    preauth()
    app = ChatApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await pilot.pause()
        await asyncio.sleep(1.0)
        await cmd(app, pilot, f"/create ops-{SUF}", 1.5)
        await cmd(app, pilot, "systeme en ligne. root access granted.", 1.2)
        await cmd(app, pilot, "quelqu'un sur le canal ?", 1.2)
        await cmd(app, pilot, "/users", 1.0)
        app.query_one("#prompt", Input).value = "cible acquise_"
        await pilot.pause()
        path = os.path.join(os.path.dirname(__file__), "hacker_repl.svg")
        app.save_screenshot(path)
        print(f"screenshot -> {path}")


if __name__ == "__main__":
    asyncio.run(main())
