from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dictate.config import Preferences, load_preferences, save_preferences
from dictate.installer import COMPONENTS, InstallerCoordinator
from dictate.platform.base import AcquisitionResult


class Platform:
    def __init__(self) -> None:
        self.components: list[str] = []

    def acquire_external_runtime(self, component: str, runner: object) -> AcquisitionResult:
        self.components.append(component)
        return AcquisitionResult(False, "unsupported local runtime acquisition")


class InstallerTests(unittest.TestCase):
    def test_verified_components_are_retained_in_fixed_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            whisper, model, ollama = (root / "whisper-server", root / "ggml-base.bin", root / "ollama")
            for path in (whisper, model, ollama):
                path.write_bytes(b"ready")
            preferences = Preferences(whisper_server_executable=str(whisper), whisper_model_path=str(model))
            coordinator = InstallerCoordinator(
                Platform(), root / "preferences.toml",
                executable_finder=lambda name: str(whisper if name == "whisper-server" else ollama),
                package_ready=lambda _requirement: True,
                ollama_ready=lambda _endpoint, _model: True,
            )
            results = coordinator.install(preferences)
        self.assertEqual(COMPONENTS, tuple(result.component for result in results))
        self.assertEqual(("retained",) * 5, tuple(result.status for result in results))

    def test_partial_model_download_is_not_retained_or_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            whisper, ollama = root / "whisper-server", root / "ollama"
            whisper.write_bytes(b"ready")
            ollama.write_bytes(b"ready")
            path = root / "preferences.toml"
            original = Preferences(whisper_server_executable=str(whisper))
            save_preferences(path, original)

            def interrupted(_url: str, temporary: Path) -> None:
                temporary.write_text("partial", encoding="utf-8")
                raise OSError("unique-sentinel-must-not-escape")

            coordinator = InstallerCoordinator(
                Platform(), path,
                executable_finder=lambda name: str(whisper if name == "whisper-server" else ollama),
                downloader=interrupted,
                package_ready=lambda _requirement: True,
                ollama_ready=lambda _endpoint, _model: True,
            )
            results = coordinator.install(original)
            self.assertEqual("failed", results[2].status)
            self.assertNotIn("unique-sentinel-must-not-escape", results[2].remediation or "")
            self.assertFalse((root / "models" / "ggml-base.bin").exists())
            self.assertEqual(original, load_preferences(path))
            self.assertFalse(list((root / "models").glob(".ggml-base.bin.*")))


if __name__ == "__main__":
    unittest.main()

