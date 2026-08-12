from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dictate.config import Preferences
from dictate.service import ReadinessResult
from dictate.startup import CombinedStartup, RuntimeLock


class Process:
    def __init__(self) -> None:
        self.stopped = False

    def start(self) -> None:
        pass

    def stop(self) -> None:
        self.stopped = True

    def running(self) -> bool:
        return not self.stopped


class StartupTests(unittest.TestCase):
    def test_lock_contention_reports_fixed_message_without_management(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dictate.lock"
            first, second = RuntimeLock(path), RuntimeLock(path)
            self.assertTrue(first.acquire())
            messages: list[str] = []
            startup = CombinedStartup(Preferences(), object(), lock=second, status=messages.append)
            self.assertEqual(1, startup.run())
            self.assertEqual(["Dictate is already running"], messages)
            first.release()

    def test_unavailable_asr_starts_only_owned_asr_and_cleans_up_on_timeout(self) -> None:
        preferences = Preferences(whisper_server_executable="/bin/echo", whisper_model_path="/tmp/model.bin")
        messages: list[str] = []
        asr = Process()
        cleanup = Process()
        clock = iter((0.0, 0.0, 31.0))
        with tempfile.TemporaryDirectory() as directory, patch("dictate.startup.WhisperServer.ready", return_value=False), patch("dictate.startup.OllamaClient.ready", return_value=True), patch("dictate.startup.check_readiness", return_value=ReadinessResult(("microphone: unavailable",), ())):
            startup = CombinedStartup(
                preferences,
                object(),
                status=messages.append,
                clock=lambda: next(clock),
                sleep=lambda _seconds: None,
                lock=RuntimeLock(Path(directory) / "lock"),
                asr_factory=lambda _endpoint, _command: asr,  # type: ignore[arg-type]
                ollama_factory=lambda _endpoint: cleanup,
            )
            self.assertEqual(1, startup.run())
        self.assertTrue(asr.stopped)
        self.assertFalse(cleanup.stopped)
        self.assertEqual(["dictate: not ready: microphone: unavailable"], messages)

    def test_unsafe_endpoint_fails_before_dependency_launch(self) -> None:
        messages: list[str] = []
        dependency = Process()
        with tempfile.TemporaryDirectory() as directory:
            startup = CombinedStartup(
                Preferences(asr_endpoint="http://example.com:8080"),
                object(),
                status=messages.append,
                lock=RuntimeLock(Path(directory) / "lock"),
                asr_factory=lambda _endpoint, _command: dependency,  # type: ignore[arg-type]
            )
            self.assertEqual(1, startup.run())
        self.assertFalse(dependency.stopped)
        self.assertEqual(["dictate: unsafe local dependency endpoint"], messages)


if __name__ == "__main__":
    unittest.main()



