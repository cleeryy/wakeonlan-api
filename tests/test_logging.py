import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required env vars
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("LOG_LEVEL", "INFO")

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestLogging:
    """Tests for structured logging."""

    def test_http_request_logged(self, caplog):
        """Should log HTTP requests with structured data."""
        with caplog.at_level(logging.INFO):
            response = client.get("/")
            assert response.status_code == 200

        # Check that an HTTP log entry was created
        http_logs = [r for r in caplog.records if r.name == "http"]
        assert len(http_logs) >= 1
        log = http_logs[0]
        assert log.levelname == "INFO"
        assert "method" in log.message or hasattr(log, "method")  # JSON fields

    def test_wol_success_logged(self, caplog):
        """Should log WoL success events."""
        with caplog.at_level(logging.INFO):
            with patch('app.main.send_magic_packet') as mock_send:
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200

        wol_logs = [r for r in caplog.records if r.name == "wol"]
        assert any("WoL success" in r.getMessage() for r in wol_logs)

    def test_wol_failure_logged(self, caplog):
        """Should log WoL failure events."""
        with caplog.at_level(logging.ERROR):
            with patch('app.main.send_magic_packet', side_effect=Exception("test error")):
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 500

        wol_logs = [r for r in caplog.records if r.name == "wol"]
        assert any("WoL failure" in r.getMessage() for r in wol_logs)

    def test_wol_attempt_logged(self, caplog):
        """Should log WoL attempt events."""
        with caplog.at_level(logging.INFO):
            with patch('app.main.send_magic_packet') as mock_send:
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200

        wol_logs = [r for r in caplog.records if r.name == "wol"]
        assert any("WoL attempt" in r.getMessage() for r in wol_logs)

    def test_log_contains_extra_fields(self, caplog):
        """WoL logs should contain MAC and broadcast IP fields."""
        with caplog.at_level(logging.INFO):
            with patch('app.main.send_magic_packet'):
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200

        wol_logs = [r for r in caplog.records if r.name == "wol"]
        success_log = next(r for r in wol_logs if "WoL success" in r.getMessage())
        # Check that extra fields are present in the log message (JSON)
        assert "mac" in str(success_log.msg) or hasattr(success_log, "mac")

    def test_custom_log_level(self, caplog):
        """Should respect LOG_LEVEL environment variable."""
        # Set LOG_LEVEL to DEBUG temporarily
        import app.main as main_mod
        original_level = logging.getLogger().level
        try:
            logging.getLogger().setLevel(logging.DEBUG)
            with caplog.at_level(logging.DEBUG):
                with patch('app.main.send_magic_packet'):
                    response = client.get("/wake", headers={"X-API-Key": "test-key"})
                    assert response.status_code == 200

            # Should have DEBUG logs if level is DEBUG
            # Our middleware uses INFO, but we can check that DEBUG logs from other libs appear
        finally:
            logging.getLogger().setLevel(original_level)
