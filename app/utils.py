import re

MAC_ADDRESS_REGEX = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


def validate_mac_address(mac: str) -> bool:
    """Validate MAC address format."""
    mac = mac.strip()
    # Check colon-separated format (XX:XX:XX:XX:XX:XX)
    if re.fullmatch(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
        return True
    # Check hyphen-separated format (XX-XX-XX-XX-XX-XX)
    if re.fullmatch(r'([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}', mac):
        return True
    return False
