from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from dictate.config import Preferences
from dictate.platform.base import PlatformAdapter
from dictate.service import ReadinessResult
from dictate.startup import CombinedStartup, RuntimeLock


class ManagedProcess:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def running(self) -> bool:
        return self.started and not self.stopped


class Service:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class CombinedStartupIntegrationTests(unittest.TestCase):
    def test_starts_missing_dependencies_then_stops_only_owned_processes(self) -> None:
        preferences = Preferences(whisper_server_executable="/bin/echo", whisper_model_path="/tmp/model.bin")
        asr, ollama = ManagedProcess(), ManagedProcess()
        service_holder: list[Service] = []
        messages: list[str] = []

        def service_factory(*args: object, **kwargs: object) -> Service:
            service = Service(*args, **kwargs)
            service_holder.append(service)
            return service

        with tempfile.TemporaryDirectory() as directory, patch("dictate.startup.WhisperServer.ready", return_value=False), patch("dictate.startup.OllamaClient.ready", return_value=False), patch("dictate.startup.shutil.which", return_value="/usr/local/bin/ollama"), patch("dictate.startup.check_readiness", return_value=ReadinessResult((), ())):
            startup = CombinedStartup(
                preferences,
                cast(PlatformAdapter, object()),
                status=messages.append,
                sleep=lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()),
                lock=RuntimeLock(Path(directory) / "lock"),
                asr_factory=lambda _endpoint, _command: asr,  # type: ignore[arg-type]
                ollama_factory=lambda _endpoint: ollama,  # type: ignore[arg-type]
                service_factory=service_factory,  # type: ignore[arg-type]
            )
            self.assertEqual(0, startup.run())

        self.assertTrue(asr.started)
        self.assertTrue(ollama.started)
        self.assertTrue(asr.stopped)
        self.assertTrue(ollama.stopped)
        self.assertTrue(service_holder[0].started)
        self.assertTrue(service_holder[0].stopped)
        self.assertEqual(["dictate: ready"], messages)


if __name__ == "__main__":
    unittest.main()


