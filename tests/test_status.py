import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required env vars
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestDeviceStatus:
    """Tests for device status endpoint."""

    def test_status_existing_device(self):
        """Should return device info for registered device."""
        # Add device first
        client.post("/devices", json={"name": "pc1", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
        response = client.get("/status/pc1", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "pc1"
        assert data["mac"] == "AA:BB:CC:DD:EE:FF"
        assert data["status"] == "registered"

    def test_status_unknown_device(self):
        """Should return 404 for non-existent device."""
        response = client.get("/status/unknown", headers={"X-API-Key": "test-key"})
        assert response.status_code == 404
        assert "not found in registry" in response.json()["detail"]["error"]

    def test_status_requires_auth(self):
        """Should require API key."""
        response = client.get("/status/pc1")  # no API key
        assert response.status_code == 403
