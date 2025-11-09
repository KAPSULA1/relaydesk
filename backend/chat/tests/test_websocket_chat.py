"""Basic WebSocket integration tests."""
import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from chat.models import Room
from chat.consumers import ChatConsumer


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_websocket_connection_accepts():
    """Authenticated clients should establish a WebSocket session."""
    user_model = get_user_model()
    user = await sync_to_async(user_model.objects.create_user)(
        username="ws_tester",
        password="pass123",
    )
    await sync_to_async(Room.objects.create)(
        name="Test Room",
        slug="test-room",
        created_by=user,
    )
    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(),
        "/ws/chat/test-room/"
    )
    communicator.scope["user"] = user
    communicator.scope["url_route"] = {"kwargs": {"room_slug": "test-room"}}
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"type": "ping"})
    await communicator.disconnect()
