"""Network utilities for local development."""
from __future__ import annotations

import socket
from typing import Optional


def get_lan_ip() -> str:
    """Best-effort detection of the host's LAN IP address.

    Returns a non-loopback IPv4 address when possible, otherwise 127.0.0.1.
    """
    ip: Optional[str] = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
    except OSError:
        ip = None

    if not ip or ip.startswith("127."):
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except OSError:
            ip = None

    return ip if ip else "127.0.0.1"
