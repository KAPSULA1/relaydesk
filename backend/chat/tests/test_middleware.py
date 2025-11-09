"""Tests for custom middleware components."""
import asyncio

import pytest
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from chat.middleware import JwtAuthMiddleware


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_jwt_middleware_authenticates_user():
    """JwtAuthMiddleware populates scope['user'] when a valid token is provided."""
    user = await sync_to_async(get_user_model().objects.create_user)(
        username="middleware_user",
        password="demoPass123",
    )
    token = AccessToken.for_user(user)

    scope = {
        "type": "websocket",
        "path": "/ws/chat/demo/",
        "query_string": f"token={token}".encode(),
        "headers": [],
        "client": ("test", 1234),
    }

    async def inner(app_scope, receive, send):
        assert app_scope["user"].is_authenticated
        return

    middleware = JwtAuthMiddleware(inner)

    async def fake_receive():
        return {"type": "websocket.connect"}

    async def fake_send(message):
        return None

    await middleware(scope, fake_receive, fake_send)


@pytest.mark.asyncio
async def test_jwt_middleware_handles_missing_token(monkeypatch):
    """Unauthenticated connections fall back to AnonymousUser."""
    scope = {
        "type": "websocket",
        "path": "/ws/chat/demo/",
        "query_string": b"",
        "headers": [],
        "client": ("test", 9999),
    }

    async def inner(app_scope, receive, send):
        assert not app_scope["user"].is_authenticated

    middleware = JwtAuthMiddleware(inner)

    async def fake_receive():
        return {"type": "websocket.connect"}

    async def fake_send(message):
        return None

    await middleware(scope, fake_receive, fake_send)
