"""Privacy boundaries for local inference and operational logging."""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from collections.abc import Mapping
from urllib.parse import ParseResult, urlparse

_CONTENT_KEYS = frozenset({"audio", "transcript", "context", "prompt", "output", "text", "content"})
_METADATA_KEYS = frozenset({"status", "error", "duration_ms", "size_bytes", "component", "reason"})
_EVENTS = frozenset({"ready", "finished", "inserted", "recovery-required", "dictation-busy", "target-unavailable", "recording-unavailable", "empty-capture", "local-processing-failed"})
_CODE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


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
    if event not in _EVENTS or invalid or prohibited:
        raise PrivacyError("ordinary logs may contain operational metadata only")
    for key in ("status", "error", "component", "reason"):
        if key in values and (not isinstance(values[key], str) or not _CODE.fullmatch(values[key])):
            raise PrivacyError("ordinary logs may contain only fixed operational codes")
    for key in ("duration_ms", "size_bytes"):
        if key in values and (isinstance(values[key], bool) or not isinstance(values[key], int) or values[key] < 0):
            raise PrivacyError("ordinary logs may contain only non-negative metadata sizes or durations")
    logger.info("%s %s", event, " ".join(f"{key}={values[key]!r}" for key in sorted(values)))

