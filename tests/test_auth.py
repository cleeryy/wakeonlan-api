import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Set required env vars BEFORE importing app to satisfy startup validation
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "")  # No auth by default

from app.main import app

client = TestClient(app)


class TestRootEndpoint:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {
            "status": 200,
            "message": "Welcome to the Wake-on-LAN API!"
        }


class TestWakeEndpointAuth:
    def test_wake_without_api_key(self):
        response = client.get("/wake")
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_wake_with_invalid_api_key(self):
        response = client.get("/wake", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_wake_with_valid_api_key(self):
        with patch('app.main.send_magic_packet') as mock_send:
            # Set API_KEY via monkeypatching the module variable
            import app.main as main_module
            original_api_key = main_module.API_KEY
            try:
                main_module.API_KEY = "valid-key"
                response = client.get("/wake", headers={"X-API-Key": "valid-key"})
                assert response.status_code == 200
                assert response.json() == {"message": "Wake-on-LAN packet sent successfully"}
                mock_send.assert_called_once_with(main_module.DEFAULT_MAC)
            finally:
                main_module.API_KEY = original_api_key

    def test_wake_mac_without_api_key(self):
        response = client.get("/wake/AA:BB:CC:DD:EE:FF")
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_wake_mac_with_valid_api_key(self):
        test_mac = "AA:BB:CC:DD:EE:FF"
        with patch('app.main.send_magic_packet') as mock_send:
            import app.main as main_module
            original_api_key = main_module.API_KEY
            try:
                main_module.API_KEY = "valid-key"
                response = client.get(f"/wake/{test_mac}", headers={"X-API-Key": "valid-key"})
                assert response.status_code == 200
                expected_msg = f"Wake-on-LAN packet sent successfully to {test_mac} device!"
                assert response.json() == {"message": expected_msg}
                mock_send.assert_called_once_with(test_mac)
            finally:
                main_module.API_KEY = original_api_key

    def test_wake_mac_with_invalid_api_key(self):
        test_mac = "AA:BB:CC:DD:EE:FF"
        response = client.get(f"/wake/{test_mac}", headers={"X-API-Key": "invalid"})
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_multiple_api_keys(self):
        with patch('app.main.send_magic_packet') as mock_send:
            import app.main as main_module
            original_api_key = main_module.API_KEY
            try:
                main_module.API_KEY = "key1,key2,key3"
                response = client.get("/wake", headers={"X-API-Key": "key2"})
                assert response.status_code == 200
                response = client.get("/wake", headers={"X-API-Key": "key4"})
                assert response.status_code == 403
            finally:
                main_module.API_KEY = original_api_key
