"""Device status checking using ping and ARP scan."""
import asyncio
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import ping3

from app.core.config import settings

# Type alias for status result
@dataclass
class StatusResult:
    """Result of a device status check."""
    online: bool
    latency_ms: Optional[float] = None
    method: str = "none"  # "ping", "arp", "none"
    open_ports: Optional[list[int]] = None


# Simple in-memory cache: {ip_address: (result, timestamp)}
_cache: dict[str, tuple[StatusResult, datetime]] = {}
_CACHE_TTL = settings.STATUS_CACHE_TTL  # seconds


def _is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system().lower() == "linux"


def _check_arp(ip: str) -> bool:
    """Check ARP cache for IP (Linux only). Returns True if found."""
    if not _is_linux():
        return False
    try:
        with open("/proc/net/arp", "r") as f:
            lines = f.readlines()
        for line in lines[1:]:  # skip header
            parts = line.split()
            if len(parts) >= 4 and parts[0] == ip:
                # Check if MAC address is present (not "00:00:00:00:00:00")
                mac = parts[3]
                if mac and mac != "00:00:00:00:00:00":
                    return True
    except Exception:
        return False
    return False


async def check_device_status(ip_address: str) -> StatusResult:
    """Check if a device is online using ping and ARP fallback.

    The check is performed in the following order:
    1. Check cache (if entry younger than CACHE_TTL)
    2. ICMP ping (async via thread)
    3. If ping fails and ARP is enabled on Linux, check ARP cache

    Args:
        ip_address: IP address of the device to check

    Returns:
        StatusResult with online status, latency (if available), and method used
    """
    # Normalize IP (strip any extra spaces)
    ip = ip_address.strip()

    # Check cache first
    now = datetime.utcnow()
    if ip in _cache:
        result, timestamp = _cache[ip]
        if now - timestamp < timedelta(seconds=_CACHE_TTL):
            return result

    # Try ICMP ping
    try:
        latency = await asyncio.to_thread(
            ping3.ping,
            ip,
            timeout=settings.STATUS_PING_TIMEOUT,
            unit="ms",
        )
        if latency is not None:
            result = StatusResult(online=True, latency_ms=latency, method="ping")
            _cache[ip] = (result, now)
            return result
        # ping3 returns None on timeout/failure
    except Exception:
        # Ping failed, continue to ARP fallback
        pass

    # ARP fallback (Linux only)
    if settings.STATUS_ARP_ENABLED and _is_linux():
        if _check_arp(ip):
            result = StatusResult(online=True, latency_ms=None, method="arp")
            _cache[ip] = (result, now)
            return result

    # Device is offline
    result = StatusResult(online=False, latency_ms=None, method="none")
    _cache[ip] = (result, now)
    return result


async def check_device_status_batch(
    ip_addresses: list[str],
) -> dict[str, StatusResult]:
    """Check status for multiple devices concurrently.

    Args:
        ip_addresses: List of IP addresses

    Returns:
        Dictionary mapping IP address to StatusResult
    """
    tasks = [check_device_status(ip) for ip in ip_addresses]
    results = await asyncio.gather(*tasks)
    return dict(zip(ip_addresses, results))


def clear_cache() -> None:
    """Clear the status cache (useful for testing)."""
    _cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics (size, entries)."""
    return {
        "size": len(_cache),
        "entries": [
            {"ip": ip, "timestamp": ts.isoformat(), "online": res.online}
            for ip, (res, ts) in _cache.items()
        ],
    }
