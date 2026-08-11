from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dictate.asr import whisper_server_command
from dictate.config import Preferences, load_preferences
from dictate.installer import InstallerCoordinator
from dictate.platform.base import AcquisitionResult


class LocalPlatform:
    def acquire_external_runtime(self, _component: str, _runner: object) -> AcquisitionResult:
        return AcquisitionResult(False, "unsupported local runtime acquisition")


class InstallerLocalComponentTests(unittest.TestCase):
    def test_downloaded_model_is_atomically_retained_with_verified_local_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            whisper, ollama = root / "whisper-server", root / "ollama"
            whisper.write_bytes(b"runtime")
            ollama.write_bytes(b"runtime")

            def download(_url: str, destination: Path) -> None:
                destination.write_bytes(b"model")

            preferences_path = root / "preferences.toml"
            coordinator = InstallerCoordinator(
                LocalPlatform(), preferences_path,
                executable_finder=lambda name: str(whisper if name == "whisper-server" else ollama),
                downloader=download,
                package_ready=lambda _requirement: True,
                ollama_ready=lambda _endpoint, _model: True,
            )
            results = coordinator.install(Preferences())
            saved = load_preferences(preferences_path)
            self.assertEqual("acquired", results[2].status)
            self.assertEqual(str(whisper), saved.whisper_server_executable)
            self.assertTrue(Path(saved.whisper_model_path or "").is_file())
            self.assertFalse(list((root / "models").glob(".ggml-base.bin.*")))
            self.assertEqual(
                (str(whisper), "--model", saved.whisper_model_path, "--host", "127.0.0.1", "--port", "8080"),
                whisper_server_command(saved),
            )


if __name__ == "__main__":
    unittest.main()


