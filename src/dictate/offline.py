"""Test-only process guard that rejects non-loopback socket connections."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any


def install_loopback_only_guard() -> None:
    """Install a process-local socket guard for offline acceptance tests."""
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection

    def allowed(address: object) -> bool:
        if not isinstance(address, tuple) or not address:
            return False
        try:
            return ipaddress.ip_address(address[0]).is_loopback
        except ValueError:
            return address[0] == "localhost"

    def connect(sock: socket.socket, address: object) -> Any:
        if not allowed(address):
            raise OSError("offline acceptance guard blocked non-loopback connection")
        return original_connect(sock, address)

    def connect_ex(sock: socket.socket, address: object) -> int:
        if not allowed(address):
            return 1
        return original_connect_ex(sock, address)

    def create_connection(address: object, *args: object, **kwargs: object) -> socket.socket:
        if not allowed(address):
            raise OSError("offline acceptance guard blocked non-loopback connection")
        return original_create_connection(address, *args, **kwargs)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.create_connection = create_connection

