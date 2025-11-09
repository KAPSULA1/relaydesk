"""Tests for health and readiness probes."""
import json
import pytest
from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory

from chat import health as health_module
from chat.models import Room, Message
from django.contrib.auth import get_user_model


@pytest.fixture(autouse=True)
def reset_cache():
    cache.clear()
    yield
    cache.clear()


def test_health_check_returns_status(client):
    """Liveness endpoint should return JSON with healthy status."""
    response = client.get('/api/health/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


def test_readiness_check_success(monkeypatch):
    """Readiness probe returns ready when DB/cache available."""
    rf = RequestFactory()

    monkeypatch.setattr(connection, 'ensure_connection', lambda: None)

    response = health_module.readiness_check(rf.get('/'))
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert payload['status'] == 'ready'
    assert payload['checks']['database'] == 'ok'
    assert payload['checks']['redis'] == 'ok'


def test_readiness_check_failure(monkeypatch):
    """Readiness should flag services that raise errors."""
    rf = RequestFactory()

    def boom():
        raise RuntimeError('db down')

    monkeypatch.setattr(connection, 'ensure_connection', boom)

    response = health_module.readiness_check(rf.get('/'))
    assert response.status_code == 503
    payload = json.loads(response.content)
    assert payload['status'] == 'not_ready'
    assert 'error' in payload['checks']['database']


@pytest.mark.django_db
def test_metrics_endpoint_counts_objects(client, django_user_model):
    """Metrics endpoint outputs counts for users, rooms, and messages."""
    user = django_user_model.objects.create_user('metrics', password='testpass')
    room = Room.objects.create(name='Metrics Room', created_by=user)
    Message.objects.create(room=room, user=user, content='Hello world')

    response = health_module.metrics(RequestFactory().get('/metrics'))
    assert response.status_code == 200
    text = response.content.decode()
    assert 'relaydesk_users_total' in text
    assert 'relaydesk_rooms_total' in text
    assert 'relaydesk_messages_total' in text
