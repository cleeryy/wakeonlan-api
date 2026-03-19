"""Tests for device management endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.crud import create_device, get_devices, update_device, delete_device
from app.models import Device
from app.schemas import DeviceCreate


@pytest.fixture
async def sample_device(db_session) -> Device:
    """Create a sample device."""
    device = await create_device(
        db_session,
        name="Test Device",
        mac_address="AA:BB:CC:DD:EE:FF",
        ip_address="192.168.1.100",
        port=9,
        enabled=True,
    )
    return device


def test_create_device(client: TestClient, test_api_key):
    """Test creating a new device."""
    from app.crud import create_api_key
    # Need to get plain key from test_api_key fixture
    # test_api_key is ApiKey object with _plain_key attribute
    plain_key = test_api_key._plain_key
    response = client.post(
        "/devices",
        json={
            "name": "New Device",
            "mac_address": "11:22:33:44:55:66",
            "ip_address": "192.168.1.101",
            "port": 9,
            "enabled": True,
        },
        headers={"X-API-Key": plain_key},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Device"
    assert data["mac_address"] == "11:22:33:44:55:66"
    assert data["ip_address"] == "192.168.1.101"


def test_list_devices(client: TestClient, test_api_key, sample_device: Device):
    """Test listing devices."""
    plain_key = test_api_key._plain_key
    response = client.get("/devices", headers={"X-API-Key": plain_key})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check sample device is in list
    assert any(d["id"] == sample_device.id for d in data)


def test_get_device(client: TestClient, test_api_key, sample_device: Device):
    """Test getting a specific device."""
    plain_key = test_api_key._plain_key
    response = client.get(
        f"/devices/{sample_device.id}", headers={"X-API-Key": plain_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_device.id
    assert data["name"] == sample_device.name


def test_update_device(client: TestClient, test_api_key, sample_device: Device):
    """Test updating a device."""
    plain_key = test_api_key._plain_key
    response = client.put(
        f"/devices/{sample_device.id}",
        json={"name": "Updated Name", "enabled": False},
        headers={"X-API-Key": plain_key},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["enabled"] is False


def test_delete_device(client: TestClient, test_api_key, sample_device: Device):
    """Test deleting a device."""
    plain_key = test_api_key._plain_key
    response = client.delete(
        f"/devices/{sample_device.id}", headers={"X-API-Key": plain_key}
    )
    assert response.status_code == 200
    # Verify deletion
    response = client.get(
        f"/devices/{sample_device.id}", headers={"X-API-Key": plain_key}
    )
    assert response.status_code == 404
