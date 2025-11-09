"""Tests for chat.jwt_auth utilities."""
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken

from chat.jwt_auth import (
    SecureTokenManager,
    set_auth_cookies,
    clear_auth_cookies,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure cache isolation between tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture()
@pytest.mark.django_db
def user():
    return get_user_model().objects.create_user(
        username="jwt_tester",
        email="jwt@example.com",
        password="supersecret123",
    )


@pytest.mark.django_db
def test_create_tokens_and_cookie_helpers(user):
    """create_tokens issues both tokens and cookie helpers set values."""
    tokens = SecureTokenManager.create_tokens(user)
    assert set(tokens.keys()) >= {"access", "refresh", "access_expires", "refresh_expires"}

    response = set_auth_cookies(HttpResponse(), tokens)
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

    cleared = clear_auth_cookies(response)
    assert cleared.cookies['access_token']['max-age'] == 0
    assert cleared.cookies['refresh_token']['max-age'] == 0


@pytest.mark.django_db
def test_rotate_refresh_token_blacklists_old(user):
    """Rotating a refresh token blacklists the previous JTI."""
    tokens = SecureTokenManager.create_tokens(user)
    old_refresh = RefreshToken(tokens["refresh"])
    old_jti = old_refresh["jti"]

    rotated = SecureTokenManager.rotate_refresh_token(tokens["refresh"])
    assert rotated is not None
    assert SecureTokenManager.is_blacklisted(old_jti)


@pytest.mark.django_db
def test_ws_token_create_and_verify(user):
    """WebSocket tokens are one-time use values stored in cache."""
    token_id = SecureTokenManager.create_ws_token(user)
    payload = SecureTokenManager.verify_ws_token(token_id)
    assert payload == {"user_id": user.id, "username": user.username, "type": "websocket"}
    # Second lookup consumes the token
    assert SecureTokenManager.verify_ws_token(token_id) is None
