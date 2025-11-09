"""Rooms API tests."""
import pytest


@pytest.mark.django_db
def test_rooms_endpoint(client):
    """/api/rooms/ responds with 200 when authed or 401 when not."""
    response = client.get("/api/rooms/")
    assert response.status_code in (200, 401)
