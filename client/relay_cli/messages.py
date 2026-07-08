"""Messages Textual échangés en interne (événements WebSocket)."""
from __future__ import annotations

from textual.message import Message


class WSEvent(Message):
    """Un événement reçu du serveur via WebSocket, réinjecté dans la boucle UI."""

    def __init__(self, data: dict):
        super().__init__()
        self.data = data


class WSStatus(Message):
    """Changement d'état de la connexion temps réel (connected/reconnecting…)."""

    def __init__(self, status: str):
        super().__init__()
        self.status = status
