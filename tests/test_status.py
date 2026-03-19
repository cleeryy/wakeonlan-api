"""Tests for device status checking."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.crud import create_device
from app.status.checker import check_device_status, clear_cache


@pytest.fixture
async def device_with_ip(db_session) -> int:
    """Create a device with an IP address."""
    device = await create_device(
        db_session,
        name="Pingable Device",
        mac_address="AA:BB:CC:DD:EE:FF",
        ip_address="8.8.8.8",
        port=9,
        enabled=True,
    )
    return device.id


def test_check_device_status_ping_success(monkeypatch):
    """Test that ping success returns online=True."""
    # Mock ping3.ping to return a latency
    monkeypatch.setattr("ping3.ping", lambda ip, timeout, unit: 12.5)
    # Run async check
    import asyncio
    result = asyncio.run(check_device_status("8.8.8.8"))
    assert result.online is True
    assert result.latency_ms == 12.5
    assert result.method == "ping"


def test_check_device_status_ping_failure_arp_fallback(monkeypatch):
    """Test that ping failure falls back to ARP on Linux."""
    # Mock ping to fail
    monkeypatch.setattr("ping3.ping", lambda ip, timeout, unit: None)
    # Mock platform to be Linux and ARP to succeed
    monkeypatch.setattr("platform.system", lambda: "Linux")
    # Mock _check_arp to return True
    from app.status import checker
    original_check_arp = checker._check_arp
    monkeypatch.setattr(checker, "_check_arp", lambda ip: True)
    import asyncio
    result = asyncio.run(check_device_status("192.168.1.1"))
    assert result.online is True
    assert result.method == "arp"
    # Restore
    monkeypatch.setattr(checker, "_check_arp", original_check_arp)


def test_check_device_status_caching(monkeypatch):
    """Test that results are cached."""
    clear_cache()
    import asyncio
    from datetime import datetime, timedelta
    # Mock ping to return a value
    call_count = 0

    def mock_ping(ip, timeout, unit):
        nonlocal call_count
        call_count += 1
        return 10.0

    monkeypatch.setattr("ping3.ping", mock_ping)
    # First call
    result1 = asyncio.run(check_device_status("1.2.3.4"))
    assert call_count == 1
    # Second call within TTL should use cache
    result2 = asyncio.run(check_device_status("1.2.3.4"))
    assert call_count == 1  # No additional ping
    assert result2.online == result1.online
    # Wait for cache to expire (mock time not easy, skip)
