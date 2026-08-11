from __future__ import annotations

import io
import logging
import unittest
from unittest.mock import patch

from dictate.config import Preferences
from dictate.platform.base import Capability
from dictate.privacy import PrivacyError, log_metadata, validate_loopback_url
from dictate.service import check_readiness


class Boundary:
    def __init__(self, *, microphone: bool = True, context: bool = True) -> None:
        self.microphone = microphone
        self.context = context

    def asr_ready(self, endpoint: str) -> Capability:
        return Capability(True)

    def ollama_model_ready(self, endpoint: str, model: str) -> Capability:
        return Capability(True)

    def microphone_ready(self, device: str) -> Capability:
        return Capability(self.microphone, "connect a microphone")

    def trigger_ready(self, trigger: str) -> Capability:
        return Capability(True)

    def placement_ready(self) -> Capability:
        return Capability(True)

    def context_ready(self) -> Capability:
        return Capability(self.context, "grant accessibility permission")


class ReadinessPrivacyTests(unittest.TestCase):
    def test_required_failure_blocks_readiness_but_context_is_only_a_limitation(self) -> None:
        self.assertFalse(check_readiness(Preferences(), Boundary(microphone=False)).ready)
        result = check_readiness(Preferences(), Boundary(context=False))
        self.assertTrue(result.ready)
        self.assertEqual(("destination context: grant accessibility permission",), result.limitations)

    def test_non_loopback_is_rejected_before_any_connection(self) -> None:
        with patch("dictate.privacy.socket.getaddrinfo") as resolver:
            with self.assertRaises(PrivacyError):
                validate_loopback_url("http://example.com:11434")
        resolver.assert_called_once()

    def test_remote_literal_is_rejected_without_dns(self) -> None:
        with patch("dictate.privacy.socket.getaddrinfo", return_value=[(None, None, None, None, ("8.8.8.8", 80))]):
            with self.assertRaises(PrivacyError):
                validate_loopback_url("http://8.8.8.8")

    def test_metadata_logging_rejects_content(self) -> None:
        stream = io.StringIO()
        logger = logging.getLogger("dictate-test")
        logger.handlers[:] = [logging.StreamHandler(stream)]
        logger.setLevel(logging.INFO)
        log_metadata(logger, "ready", {"component": "asr", "duration_ms": 12})
        self.assertIn("component", stream.getvalue())
        with self.assertRaises(PrivacyError):
            log_metadata(logger, "finished", {"transcript": "unique-sentinel"})
        self.assertNotIn("unique-sentinel", stream.getvalue())


if __name__ == "__main__":
    unittest.main()

