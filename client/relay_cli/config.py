"""Client configuration and persistent token storage."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("RELAY_CONFIG_DIR", Path.home() / ".relay"))
CONFIG_FILE = CONFIG_DIR / "config.json"

# Serveur par défaut = la prod. Surchargez avec la variable d'env RELAY_API
# (ex. http://127.0.0.1:8000 en développement) ou via `relay chat --api ...`.
DEFAULT_API = os.environ.get("RELAY_API", "https://api-chat.hanifcode.fr")


def _http_to_ws(url: str) -> str:
    return url.replace("https://", "wss://").replace("http://", "ws://")


@dataclass
class Session:
    api_url: str = DEFAULT_API
    access: str = ""
    refresh: str = ""
    username: str = ""

    @property
    def ws_url(self) -> str:
        return _http_to_ws(self.api_url)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.access)

    # --- persistence ---------------------------------------------------

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(
                {
                    "api_url": self.api_url,
                    "access": self.access,
                    "refresh": self.refresh,
                    "username": self.username,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def clear(self) -> None:
        self.access = ""
        self.refresh = ""
        self.username = ""
        self.save()

    @classmethod
    def load(cls) -> "Session":
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return cls(
                    api_url=data.get("api_url", DEFAULT_API),
                    access=data.get("access", ""),
                    refresh=data.get("refresh", ""),
                    username=data.get("username", ""),
                )
            except (json.JSONDecodeError, OSError):
                pass
        return cls()
