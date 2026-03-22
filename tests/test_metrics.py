import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required env vars
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("METRICS_ENABLED", "true")

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestMetrics:
    """Tests for Prometheus metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Should return metrics in Prometheus text format."""
        with patch('app.main.send_magic_packet'):
            # Make some requests to generate metrics
            client.get("/wake", headers={"X-API-Key": "test-key"})
            client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
            client.post("/devices", json={"name": "test-pc", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})

        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        content = response.text
        
        # Check for presence of expected metrics
        assert "wol_requests_total" in content
        assert "wol_success_total" in content
        assert "wol_failure_total" in content
        assert "wol_retries_total" in content
        assert "wol_duration_seconds" in content

    def test_metrics_collects_success_and_failure(self):
        """Should track both successful and failed WoL attempts."""
        with patch('app.main.send_magic_packet') as mock_send:
            # One success
            client.get("/wake", headers={"X-API-Key": "test-key"})
            
            # One failure
            mock_send.side_effect = Exception("Network error")
            response = client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
            assert response.status_code == 500

        response = client.get("/metrics")
        content = response.text
        
        # Should have success and failure metrics
        assert "wol_success_total" in content
        assert "wol_failure_total" in content

    def test_metrics_endpoint_disabled_when_metrics_disabled(self):
        """Should return 404 when METRICS_ENABLED=false."""
        import app.main as main_mod
        original = main_mod.METRICS_ENABLED
        main_mod.METRICS_ENABLED = False
        try:
            response = client.get("/metrics")
            assert response.status_code == 404
        finally:
            main_mod.METRICS_ENABLED = original

    def test_metrics_retries_tracked(self):
        """Should track retry attempts."""
        with patch('app.main.send_magic_packet') as mock_send:
            # Fail twice then succeed (2 retries)
            mock_send.side_effect = [Exception("fail"), Exception("fail"), None]
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200

        response = client.get("/metrics")
        content = response.text
        # Should have retry metric
        assert "wol_retries_total" in content

    def test_batch_wake_metrics(self):
        """Should track batch wake operations."""
        with patch('app.main.send_magic_packet'):
            response = client.post(
                "/wake/batch",
                json={"mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]},
                headers={"X-API-Key": "test-key"}
            )
            assert response.status_code == 200

        response = client.get("/metrics")
        content = response.text
        # Should contain batch endpoint metric
        assert 'endpoint="/wake/batch"' in content

    def test_metrics_have_labels(self):
        """Should label metrics by endpoint."""
        with patch('app.main.send_magic_packet'):
            client.get("/wake", headers={"X-API-Key": "test-key"})
            
        response = client.get("/metrics")
        content = response.text
        # Check that endpoint labels are present
        assert 'endpoint="/wake"' in content

    def test_wake_by_name_metrics(self):
        """Should track wake by name endpoint."""
        # First add a device
        client.post("/devices", json={"name": "my-pc", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
        
        with patch('app.main.send_magic_packet'):
            response = client.get("/wake/device/my-pc", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200

        response = client.get("/metrics")
        content = response.text
        assert 'endpoint="/wake/device/my-pc"' in content

    def test_metrics_counter_increments_multiple_requests(self):
        """Should increment counters correctly across multiple requests."""
        with patch('app.main.send_magic_packet'):
            for _ in range(3):
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200

        response = client.get("/metrics")
        content = response.text
        # The counter should show at least 3 (exact formatting may vary)
        # Look for wol_requests_total with endpoint="/wake" and status="success"
        lines = content.splitlines()
        # The line should be like: wol_requests_total{endpoint="/wake",status="success"} 3.0
        wake_requests_lines = [l for l in lines if 'wol_requests_total{endpoint="/wake",status="success"}' in l]
        assert len(wake_requests_lines) > 0
        # The value should be 3.0
        value = float(wake_requests_lines[0].split()[-1])
        assert value >= 3.0
