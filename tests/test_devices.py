import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set env vars before importing app
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")

from app.main import app
import app.main as main_mod

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


@pytest.fixture(autouse=True)
def reset_device_registry(tmp_path):
    """Reset device registry before each test using a temporary file."""
    temp_file = tmp_path / "test_devices.json"
    new_registry = main_mod.device_registry.__class__(str(temp_file))
    main_mod.device_registry = new_registry
    yield


class TestDeviceRegistry:
    """Tests for device registry endpoints."""

    def test_list_devices_empty(self):
        response = client.get("/devices", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        assert response.json() == {}

    def test_add_device_success(self):
        response = client.post(
            "/devices",
            json={"name": "pc1", "mac": "AA:BB:CC:DD:EE:FF"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        assert response.json() == {"message": "Device 'pc1' added successfully"}

        response = client.get("/devices", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        assert response.json() == {"pc1": "AA:BB:CC:DD:EE:FF"}

    def test_add_device_invalid_mac(self):
        response = client.post(
            "/devices",
            json={"name": "pc1", "mac": "invalid"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid MAC address format" in data["detail"]["error"]

    def test_add_device_duplicate_name(self):
        client.post("/devices", json={"name": "pc1", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
        response = client.post(
            "/devices",
            json={"name": "pc1", "mac": "11:22:33:44:55:66"},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"]["error"]

    def test_delete_device_success(self):
        client.post("/devices", json={"name": "pc1", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
        response = client.delete("/devices/pc1", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        assert response.json() == {"message": "Device 'pc1' deleted successfully"}
        response = client.get("/devices", headers={"X-API-Key": "test-key"})
        assert response.status_code == 200
        assert response.json() == {}

    def test_delete_device_not_found(self):
        response = client.delete("/devices/nonexistent", headers={"X-API-Key": "test-key"})
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]["error"]

    def test_wake_device_by_name_success(self):
        with patch('app.main.send_magic_packet') as mock_send:
            client.post("/devices", json={"name": "pc1", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
            response = client.get("/wake/device/pc1", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert "Wake-on-LAN packet sent successfully to pc1" in response.json()["message"]
            mock_send.assert_called_once_with("AA:BB:CC:DD:EE:FF")

    def test_wake_device_by_name_not_found(self):
        response = client.get("/wake/device/nonexistent", headers={"X-API-Key": "test-key"})
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found in registry" in data["detail"]["error"]

    def test_device_registry_persistence(self):
        import app.main as main_mod
        import tempfile
        persist_dir = Path(tempfile.mkdtemp())
        persist_file = persist_dir / "persist_devices.json"
        new_reg = main_mod.device_registry.__class__(str(persist_file))
        main_mod.device_registry = new_reg

        client.post("/devices", json={"name": "persistent-pc", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
        assert persist_file.exists()
        import json
        with open(persist_file) as f:
            data = json.load(f)
        assert data == {"persistent-pc": "AA:BB:CC:DD:EE:FF"}
