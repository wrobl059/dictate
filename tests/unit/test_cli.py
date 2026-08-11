from __future__ import annotations

import contextlib
import io
import unittest
from unittest.mock import patch

from dictate.audio import AudioInputDevice
from dictate.installer import ComponentResult
from dictate.service import ReadinessResult


class CliTests(unittest.TestCase):
    def invoke(self, arguments: list[str]) -> tuple[int, str, str]:
        from dictate.cli import main

        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(arguments)
        return result, stdout.getvalue(), stderr.getvalue()

    @patch("dictate.cli.list_input_devices", return_value=(AudioInputDevice("7", "Built-in Microphone"),))
    def test_devices_lists_identifiers_without_recording(self, _devices: object) -> None:
        result, stdout, stderr = self.invoke(["devices"])
        self.assertEqual(0, result)
        self.assertEqual("7\tBuilt-in Microphone\n", stdout)
        self.assertEqual("", stderr)

    @patch("dictate.cli.check_readiness", return_value=ReadinessResult((), ("destination context: grant-accessibility",)))
    @patch("dictate.cli.current_platform", return_value=object())
    def test_setup_reports_ready_with_optional_context_limitation(self, _platform: object, _readiness: object) -> None:
        result, stdout, stderr = self.invoke(["setup"])
        self.assertEqual(0, result)
        self.assertEqual("setup: ready\n", stdout)
        self.assertIn("limitation: destination context: grant-accessibility", stderr)

    @patch("dictate.cli.check_readiness", return_value=ReadinessResult(("microphone: connect-a-microphone",), ()))
    @patch("dictate.cli.current_platform", return_value=object())
    def test_doctor_returns_nonzero_content_free_required_failure(self, _platform: object, _readiness: object) -> None:
        result, stdout, stderr = self.invoke(["doctor"])
        self.assertEqual(1, result)
        self.assertEqual("", stdout)
        self.assertEqual("doctor: not ready: microphone: connect-a-microphone\n", stderr)

    @patch("dictate.cli.load_preferences")
    @patch("dictate.cli.InstallerCoordinator")
    @patch("dictate.cli.check_readiness", return_value=ReadinessResult((), ()))
    @patch("dictate.cli.current_platform", return_value=object())
    def test_explicit_setup_prints_ordered_statuses_before_final_ready(self, _platform: object, _readiness: object, coordinator_type: object, load: object) -> None:
        from dictate.config import Preferences

        preferences = Preferences()
        load.return_value = preferences  # type: ignore[attr-defined]
        coordinator_type.return_value.install.return_value = (  # type: ignore[attr-defined]
            ComponentResult("python-dependencies", "retained"),
            ComponentResult("whisper-runtime", "acquired"),
        )
        result, stdout, stderr = self.invoke(["setup", "--install-dependencies"])
        self.assertEqual(0, result)
        self.assertEqual("setup: ready\n", stdout)
        self.assertLess(stderr.index("python-dependencies: retained"), stderr.index("whisper-runtime: acquired"))

    @patch("dictate.cli.InstallerCoordinator")
    @patch("dictate.cli.current_platform", return_value=object())
    def test_failed_install_never_reports_ready(self, _platform: object, coordinator_type: object) -> None:
        coordinator_type.return_value.install.return_value = (ComponentResult("whisper-model", "failed", "network unavailable"),)  # type: ignore[attr-defined]
        result, stdout, stderr = self.invoke(["setup", "--install-dependencies"])
        self.assertEqual(1, result)
        self.assertEqual("", stdout)
        self.assertIn("whisper-model: failed", stderr)


if __name__ == "__main__":
    unittest.main()

