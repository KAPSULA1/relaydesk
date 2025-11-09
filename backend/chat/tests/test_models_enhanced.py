"""Tests for the optional enhanced models module."""
from types import SimpleNamespace
import importlib.util
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db import models as django_models

MODULE_PATH = Path(__file__).resolve().parents[1] / "models_enhanced.py"
spec = importlib.util.spec_from_file_location(
    "chat.models_enhanced_testcopy",
    MODULE_PATH,
)
enhanced = importlib.util.module_from_spec(spec)
_register_model = django_apps.register_model


def _safe_register(app_label, model):
    if app_label == 'chat' and model.__module__.startswith('chat.models_enhanced_testcopy'):
        return  # Skip registering shadow models to avoid conflicts
    return _register_model(app_label, model)


django_apps.register_model = _safe_register
spec.loader.exec_module(enhanced)
django_apps.register_model = _register_model


def test_user_profile_str():
    """UserProfile __str__ should include username."""
    dummy_user = get_user_model()(username='alice')
    profile = enhanced.UserProfile(user=dummy_user)
    assert "alice" in str(profile)


def test_room_category_str():
    """RoomCategory __str__ returns its display name."""
    category = enhanced.RoomCategory(name='Product')
    assert str(category) == 'Product'


def test_room_save_generates_unique_slug(monkeypatch):
    """Room.save() should auto-populate slug even without DB writes."""
    call_counts = {'filter_calls': 0}

    class DummyQuerySet:
        def exists(self):
            call_counts['filter_calls'] += 1
            return call_counts['filter_calls'] == 1  # First call says slug exists

    def fake_filter(*args, **kwargs):
        return DummyQuerySet()

    monkeypatch.setattr(enhanced.Room.objects, 'filter', fake_filter)
    monkeypatch.setattr(django_models.Model, 'save', lambda self, *a, **k: None)

    room = enhanced.Room(name='Team Sync', created_by=get_user_model()(username='owner'))
    room.save()
    assert room.slug.startswith('team-sync')


def test_get_or_create_dm_creates_when_missing(monkeypatch):
    """get_or_create_dm should create a DM room when none exists."""
    created_rooms = {}

    class DummyQS:
        def filter(self, *args, **kwargs):
            return self
        def exists(self):
            return False

    def fake_filter(*args, **kwargs):
        return DummyQS()

    def fake_create(**kwargs):
        room = SimpleNamespace(**kwargs)
        created_rooms['room'] = room
        room.dm_participants = SimpleNamespace(add=lambda *a, **k: None)
        return room

    monkeypatch.setattr(enhanced.Room.objects, 'filter', fake_filter)
    monkeypatch.setattr(enhanced.Room.objects, 'create', fake_create)
    monkeypatch.setattr(enhanced.RoomMember, 'objects', SimpleNamespace(create=lambda **k: None))

    room, created = enhanced.Room.get_or_create_dm(SimpleNamespace(username='a'), SimpleNamespace(username='b'))
    assert created is True
    assert room is created_rooms['room']


def test_room_member_mark_as_read(monkeypatch):
    """mark_as_read should call save with updated timestamp."""
    calls = {}

    def fake_save(self, update_fields=None):
        calls['update_fields'] = update_fields

    monkeypatch.setattr(enhanced.RoomMember, 'save', fake_save)
    member = enhanced.RoomMember()
    member.mark_as_read()
    assert calls['update_fields'] == ['last_read_at']
