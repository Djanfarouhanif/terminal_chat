import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Channel, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """Real-time consumer for a single channel room.

    Client -> server events (JSON `{"type": ..., ...}`):
        message  {content}
        typing   {}
        edit     {id, content}
        delete   {id}

    Server -> client events mirror the PRD: user_join, user_leave,
    message, typing, edit, delete.
    """

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        self.channel_slug = self.scope["url_route"]["kwargs"]["channel_name"]
        self.group_name = f"chat_{self.channel_slug}"

        self.channel_obj = await self._get_channel(self.channel_slug)
        if self.channel_obj is None:
            await self.close(code=4404)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "user_join", "username": self.user.username},
        )

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "user_leave", "username": self.user.username},
            )
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        event = content.get("type")

        if event == "message":
            text = (content.get("content") or "").strip()
            if not text:
                return
            msg = await self._save_message(text)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "message",
                    "id": msg.id,
                    "sender": self.user.username,
                    "sender_id": self.user.id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                },
            )
        elif event == "typing":
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "typing", "username": self.user.username},
            )
        elif event == "edit":
            msg = await self._edit_message(content.get("id"), content.get("content"))
            if msg:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "edit",
                        "id": msg.id,
                        "content": msg.content,
                    },
                )
        elif event == "delete":
            deleted_id = await self._delete_message(content.get("id"))
            if deleted_id:
                await self.channel_layer.group_send(
                    self.group_name,
                    {"type": "delete", "id": deleted_id},
                )

    # --- group event handlers (broadcast -> client) ---------------------

    async def message(self, event):
        await self.send_json(event)

    async def typing(self, event):
        if event["username"] != self.user.username:
            await self.send_json(event)

    async def user_join(self, event):
        await self.send_json(event)

    async def user_leave(self, event):
        await self.send_json(event)

    async def edit(self, event):
        await self.send_json(event)

    async def delete(self, event):
        await self.send_json(event)

    # --- database helpers ----------------------------------------------

    @database_sync_to_async
    def _get_channel(self, slug):
        return Channel.objects.filter(name=slug).first()

    @database_sync_to_async
    def _save_message(self, text):
        return Message.objects.create(
            channel=self.channel_obj, sender=self.user, content=text
        )

    @database_sync_to_async
    def _edit_message(self, msg_id, text):
        text = (text or "").strip()
        if not text:
            return None
        msg = Message.objects.filter(id=msg_id, sender=self.user).first()
        if not msg:
            return None
        msg.content = text
        msg.edited = True
        msg.save(update_fields=["content", "edited", "updated_at"])
        return msg

    @database_sync_to_async
    def _delete_message(self, msg_id):
        msg = Message.objects.filter(id=msg_id, sender=self.user).first()
        if not msg:
            return None
        msg.delete()
        return msg_id


class DMConsumer(AsyncJsonWebsocketConsumer):
    """Connexion temps réel personnelle : reçoit les messages privés (DM).

    Chaque utilisateur rejoint le groupe `dm_<id>`. L'API `/api/dm` pousse
    chaque nouveau message privé dans les groupes de l'expéditeur ET du
    destinataire, qui le reçoivent instantanément.
    """

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return
        self.group_name = f"dm_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dm_message(self, event):
        await self.send_json(event)
