"""Serializer validation tests."""
import pytest
from django.contrib.auth import get_user_model

from chat import serializers
from chat.models import Room, Message


@pytest.mark.django_db
def test_user_registration_serializer_validates_password_match():
    data = {
        'username': 'serial_tester',
        'email': 'serial@example.com',
        'password': 'ComplexPass1',
        'password_confirm': 'Mismatch',
    }
    serializer = serializers.UserRegistrationSerializer(data=data)
    assert not serializer.is_valid()
    assert 'password' in serializer.errors


@pytest.mark.django_db
def test_user_registration_serializer_creates_user():
    payload = {
        'username': 'serial_ok',
        'email': 'serial_ok@example.com',
        'password': 'ComplexPass1',
        'password_confirm': 'ComplexPass1',
    }
    serializer = serializers.UserRegistrationSerializer(data=payload)
    assert serializer.is_valid(raise_exception=True)
    user = serializer.save()
    assert get_user_model().objects.filter(id=user.id).exists()


@pytest.mark.django_db
def test_room_create_serializer_enforces_uniqueness(django_user_model):
    owner = django_user_model.objects.create_user('room_owner', password='pass123')
    Room.objects.create(name='Focus Room', created_by=owner)

    serializer = serializers.RoomCreateSerializer(data={'name': 'focus room'})
    assert not serializer.is_valid()
    assert 'Room already exists' in serializer.errors['name'][0]


@pytest.mark.django_db
def test_message_create_serializer_rejects_empty():
    serializer = serializers.MessageCreateSerializer(data={'content': '   '})
    assert not serializer.is_valid()
    assert serializer.errors['content'][0] in (
        'Message cannot be empty',
        'This field may not be blank.'
    )


@pytest.mark.django_db
def test_message_serializer_outputs_username(django_user_model):
    user = django_user_model.objects.create_user('msg_user', password='pass123')
    room = Room.objects.create(name='Serializer Room', created_by=user)
    message = Message.objects.create(room=room, user=user, content='Hello!')
    data = serializers.MessageSerializer(message).data
    assert data['username'] == 'msg_user'
