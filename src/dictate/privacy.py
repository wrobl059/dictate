"""Privacy boundaries for local inference and operational logging."""

from __future__ import annotations

import ipaddress
import logging
import socket
from collections.abc import Mapping
from urllib.parse import ParseResult, urlparse

_CONTENT_KEYS = frozenset({"audio", "transcript", "context", "prompt", "output", "text", "content"})
_METADATA_KEYS = frozenset({"status", "error", "duration_ms", "size_bytes", "component", "reason"})


class PrivacyError(ValueError):
    """Raised before data could be sent to an unsafe endpoint."""


def validate_loopback_url(url: str) -> ParseResult:
    parsed = urlparse(url)
    if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
        raise PrivacyError("inference endpoint must be an unauthenticated http loopback URL")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, parsed.port or 80, type=socket.SOCK_STREAM)}
    except socket.gaierror as error:
        raise PrivacyError("inference endpoint host could not be resolved") from error
    if not addresses or any(not ipaddress.ip_address(address).is_loopback for address in addresses):
        raise PrivacyError("inference endpoint must resolve only to loopback addresses")
    return parsed


def log_metadata(logger: logging.Logger, event: str, metadata: Mapping[str, object] | None = None) -> None:
    """Emit allow-listed operational metadata and reject content-bearing fields."""
    values = dict(metadata or {})
    invalid = set(values) - _METADATA_KEYS
    prohibited = set(values) & _CONTENT_KEYS
    if invalid or prohibited:
        raise PrivacyError("ordinary logs may contain operational metadata only")
    logger.info("%s %s", event, " ".join(f"{key}={values[key]!r}" for key in sorted(values)))

