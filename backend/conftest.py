import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
  """Reusable DRF API client fixture."""
  return APIClient()
