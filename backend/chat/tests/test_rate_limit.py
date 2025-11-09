"""Tests for the RateLimitMiddleware behavior."""
import pytest
from django.test import RequestFactory
from django.core.cache import cache

from chat.rate_limit import RateLimitMiddleware


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def rf():
    return RequestFactory()


def test_rate_limit_blocks_after_threshold(rf):
    """Middleware should return HTTP 429 when limits exceeded."""
    middleware = RateLimitMiddleware(lambda request: request)
    middleware.RATE_LIMITS['default'] = (2, 60)

    request = rf.get('/some-endpoint/')
    request.META['REMOTE_ADDR'] = '127.0.0.1'

    assert middleware.process_request(request) is None
    assert middleware.process_request(request) is None

    import json

    response = middleware.process_request(request)
    assert response.status_code == 429
    payload = json.loads(response.content)
    assert 'retry_after' in payload


def test_get_client_id_prefers_authenticated_user(rf, django_user_model):
    """Authenticated users are tracked by user id instead of IP."""
    user = django_user_model.objects.create_user('rateuser', password='pass123')
    request = rf.get('/api/rooms/')
    request.user = user
    client_id = RateLimitMiddleware(lambda request: request).get_client_id(request)
    assert client_id == f"user:{user.id}"


def test_get_client_id_falls_back_to_ip(rf):
    """Unauthenticated requests fall back to the remote IP."""
    request = rf.get('/api/rooms/')
    request.META['REMOTE_ADDR'] = '10.0.0.9'
    client_id = RateLimitMiddleware(lambda request: request).get_client_id(request)
    assert client_id == 'ip:10.0.0.9'
