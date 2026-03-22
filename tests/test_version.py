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
os.environ.setdefault("API_VERSION", "1.0")

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestVersionEndpoint:
    """Tests for API version endpoint."""

    def test_version_endpoint_returns_version(self):
        """Should return API version in JSON format."""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "wakeonlan-api"
        assert "version" in data
        # Version should be a string; exact value from env
        assert isinstance(data["version"], str)

    def test_version_endpoint_uses_env_var(self):
        """Should use API_VERSION environment variable."""
        import app.main as main_mod
        original = main_mod.API_VERSION
        main_mod.API_VERSION = "2.3.4"
        try:
            response = client.get("/version")
            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "2.3.4"
        finally:
            main_mod.API_VERSION = original

    def test_version_endpoint_not_authenticated(self):
        """Should be accessible without authentication."""
        response = client.get("/version")
        assert response.status_code == 200
