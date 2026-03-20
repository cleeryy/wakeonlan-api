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
# Use default RATE_LIMIT_REQUESTS=5 from app configuration

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_send_magic_packet(monkeypatch):
    """Mock send_magic_packet to avoid actual network calls during tests."""
    def mock_send(*args, **kwargs):
        pass
    monkeypatch.setattr('app.main.send_magic_packet', mock_send)


@pytest.fixture(autouse=True)
def reset_limiter_before_and_after():
    """Reset rate limiter before and after each test to ensure clean state."""
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


class TestRateLimiting:
    """Tests for rate limiting on /wake endpoints."""

    def test_rate_limit_exceeded_returns_429(self):
        """Should return 429 when rate limit is exceeded."""
        # Use default rate limit of 5
        rate_limit = 5
        
        # Make requests up to the limit (should all succeed)
        for i in range(rate_limit):
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        # Next request should be rate limited
        response = client.get("/wake", headers={"X-API-Key": "test-key"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["error"]

    def test_rate_limit_message_format(self):
        """Should return proper error message with rate limit details."""
        rate_limit = 5
        
        # Exceed rate limit
        for _ in range(rate_limit + 1):
            client.get("/wake", headers={"X-API-Key": "test-key"})
        
        response = client.get("/wake", headers={"X-API-Key": "test-key"})
        data = response.json()
        assert "error" in data
        assert f"Maximum {rate_limit}" in data["error"]
        assert "requests per" in data["error"]

    def test_rate_limit_applies_to_mac_endpoint(self):
        """Should rate limit /wake/{mac} endpoint as well."""
        rate_limit = 5
        
        # Exceed limit on specific MAC endpoint
        for i in range(rate_limit):
            response = client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        response = client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
        assert response.status_code == 429

    def test_rate_limit_by_ip(self):
        """Should rate limit based on client IP address."""
        rate_limit = 5
        
        # All requests from same client (test client) should be tracked together
        for i in range(rate_limit):
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        response = client.get("/wake", headers={"X-API-Key": "test-key"})
        assert response.status_code == 429

    def test_different_api_keys_same_ip_shared_limit(self):
        """Should share rate limit across API keys from same IP."""
        rate_limit = 5
        
        # Set multiple valid keys
        import app.main as main_module
        original_api_key = main_module.API_KEY
        try:
            main_module.API_KEY = "test-key,another-key"
            
            # Use first key until limit
            for i in range(rate_limit):
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200, f"Request {i+1} should succeed"
            
            # Use second key - should be rate limited (same IP)
            response = client.get("/wake", headers={"X-API-Key": "another-key"})
            assert response.status_code == 429
        finally:
            main_module.API_KEY = original_api_key

    def test_root_endpoint_not_rate_limited(self):
        """Root endpoint should not be rate limited."""
        # Make many requests to root - should all succeed
        for _ in range(10):
            response = client.get("/")
            assert response.status_code == 200
