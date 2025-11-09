"""Advanced integration tests for API viewsets."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from chat.models import Room, Message


@pytest.fixture
@pytest.mark.django_db
def auth_client(django_user_model):
    user = django_user_model.objects.create_user('api_user', password='pass12345')
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db
def test_room_crud_flow(auth_client):
    """Authenticated user can create and retrieve rooms."""
    client, user = auth_client
    create_resp = client.post('/api/rooms/', {'name': 'Project Alpha', 'description': 'Secret'}, format='json')
    assert create_resp.status_code == 201
    slug = Room.objects.get(name='Project Alpha').slug

    list_resp = client.get('/api/rooms/')
    assert list_resp.status_code == 200
    assert any(room['slug'] == slug for room in list_resp.data)

    detail_resp = client.get(f'/api/rooms/{slug}/')
    assert detail_resp.status_code == 200
    assert detail_resp.data['name'] == 'Project Alpha'


@pytest.mark.django_db
def test_message_creation_and_listing(auth_client):
    """MessageViewSet allows posting and querying room messages."""
    client, user = auth_client
    room = Room.objects.create(name='Message Room', created_by=user)

    create_resp = client.post('/api/messages/', {'content': 'hello world', 'room_slug': room.slug}, format='json')
    assert create_resp.status_code == 201

    list_resp = client.get(f'/api/messages/?room_slug={room.slug}')
    assert list_resp.status_code == 200
    assert list_resp.data[0]['content'] == 'hello world'


@pytest.mark.django_db
def test_room_presence_endpoint(auth_client, django_user_model):
    """room_presence returns cached online user list."""
    client, user = auth_client
    room = Room.objects.create(name='Presence Room', created_by=user)

    from django.core.cache import cache
    cache.set(f'room_presence:{room.slug}', [{'id': user.id, 'username': user.username}], timeout=30)

    resp = client.get(f'/api/presence/{room.slug}/')
    assert resp.status_code == 200
    assert resp.data['count'] == 1
    assert resp.data['online_users'][0]['username'] == user.username
