import json
import os
from pathlib import Path
from typing import Dict, Optional

from .utils import validate_mac_address


class DeviceRegistry:
    """Simple in-memory device registry with JSON file persistence."""

    def __init__(self, file_path: str = "devices.json"):
        self.file_path = Path(file_path)
        self.devices: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load devices from JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.devices = data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load devices file: {e}")
                self.devices = {}
        else:
            self.devices = {}

    def _save(self) -> None:
        """Save devices to JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.devices, f, indent=2)
        except IOError as e:
            print(f"Error: Failed to save devices file: {e}")

    def add(self, name: str, mac: str) -> bool:
        """
        Add a new device.
        
        Returns False if name already exists or MAC invalid.
        """
        if name in self.devices:
            return False
        if not validate_mac_address(mac):
            return False
        self.devices[name] = mac
        self._save()
        return True

    def remove(self, name: str) -> bool:
        """Remove a device by name."""
        if name not in self.devices:
            return False
        del self.devices[name]
        self._save()
        return True

    def get(self, name: str) -> Optional[str]:
        """Get MAC address by device name."""
        return self.devices.get(name)

    def list_devices(self) -> Dict[str, str]:
        """Return all devices as dict."""
        return self.devices.copy()

    def exists(self, name: str) -> bool:
        """Check if device exists."""
        return name in self.devices

    def reset(self) -> None:
        """Clear all devices and save empty registry (for testing)."""
        self.devices = {}
        self._save()
