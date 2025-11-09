"""Authentication API tests."""
import pytest


@pytest.mark.django_db
def test_auth_me_requires_authentication(client):
    """/api/auth/me/ should reject anonymous users with 401."""
    response = client.get("/api/auth/me/")
    assert response.status_code == 401
