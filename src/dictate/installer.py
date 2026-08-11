"""Explicit, content-free acquisition of Dictate's local default pipeline."""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, Protocol

from dictate.cleanup import OllamaClient
from dictate.config import DEFAULT_OLLAMA_MODEL, DEFAULT_WHISPER_MODEL, Preferences, save_preferences

ComponentStatus = Literal["retained", "acquired", "failed", "unsupported"]
PYTHON_DEPENDENCIES = ("sounddevice==0.5.5", "pynput==1.8.2")
COMPONENTS = ("python-dependencies", "whisper-runtime", "whisper-model", "ollama-runtime", "ollama-model")
DEFAULT_WHISPER_MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"


@dataclass(frozen=True)
class ComponentResult:
    """A command-scoped status which never includes paths, URLs, or tool output."""

    component: str
    status: ComponentStatus
    remediation: str | None = None


class RuntimeAcquirer(Protocol):
    def acquire_external_runtime(self, component: str, runner: Callable[[Sequence[str]], bool]) -> object: ...


class InstallerCoordinator:
    """Acquire only missing default components after an explicit CLI request."""

    def __init__(
        self,
        platform: RuntimeAcquirer,
        preferences_path: Path,
        *,
        executable_finder: Callable[[str], str | None] | None = None,
        runner: Callable[[Sequence[str]], bool] | None = None,
        downloader: Callable[[str, Path], None] | None = None,
        package_ready: Callable[[str], bool] | None = None,
        ollama_ready: Callable[[str, str], bool] | None = None,
        saver: Callable[[Path, Preferences], None] = save_preferences,
        model_url: str = DEFAULT_WHISPER_MODEL_URL,
    ) -> None:
        self._platform = platform
        self._preferences_path = preferences_path
        self._executable_finder = executable_finder or self._find_executable
        self._runner = runner or self._run
        self._downloader = downloader or self._download
        self._package_ready = package_ready or self._package_is_ready
        self._ollama_ready = ollama_ready or self._ollama_is_ready
        self._saver = saver
        self._model_url = model_url

    def install(self, preferences: Preferences) -> tuple[ComponentResult, ...]:
        """Return fixed-order component outcomes; never claim final service readiness."""
        results: list[ComponentResult] = [self._python_dependencies()]
        executable, runtime_result = self._whisper_runtime(preferences)
        results.append(runtime_result)
        model, model_result = self._whisper_model(preferences)
        results.append(model_result)
        if executable and model:
            try:
                self._saver(
                    self._preferences_path,
                    replace(preferences, whisper_server_executable=str(executable), whisper_model_path=str(model)),
                )
            except OSError:
                results[-1] = ComponentResult("whisper-model", "failed", "could not save verified local runtime settings")
        results.append(self._external_runtime("ollama-runtime", "ollama"))
        results.append(self._ollama_model(preferences))
        return tuple(results)

    def _python_dependencies(self) -> ComponentResult:
        return ComponentResult(
            "python-dependencies",
            "retained" if all(self._package_ready(requirement) for requirement in PYTHON_DEPENDENCIES) else "failed",
            None if all(self._package_ready(requirement) for requirement in PYTHON_DEPENDENCIES) else "rerun explicit setup to repair Python dependencies",
        )

    def _whisper_runtime(self, preferences: Preferences) -> tuple[Path | None, ComponentResult]:
        candidate = self._usable_file(preferences.whisper_server_executable) or self._which_file("whisper-server")
        if candidate:
            return candidate, ComponentResult("whisper-runtime", "retained")
        acquired = self._platform.acquire_external_runtime("whisper-runtime", self._runner)
        if not acquired.acquired:
            return None, ComponentResult("whisper-runtime", "unsupported" if acquired.remediation == "unsupported local runtime acquisition" else "failed", acquired.remediation)
        candidate = self._which_file("whisper-server")
        if not candidate:
            return None, ComponentResult("whisper-runtime", "failed", "local whisper runtime was not available after installation")
        return candidate, ComponentResult("whisper-runtime", "acquired")

    def _whisper_model(self, preferences: Preferences) -> tuple[Path | None, ComponentResult]:
        candidate = self._usable_file(preferences.whisper_model_path)
        if candidate:
            return candidate, ComponentResult("whisper-model", "retained")
        destination = self._preferences_path.parent / "models" / DEFAULT_WHISPER_MODEL
        if destination.is_file() and destination.stat().st_size > 0:
            return destination, ComponentResult("whisper-model", "retained")
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{DEFAULT_WHISPER_MODEL}.", dir=destination.parent)
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            self._downloader(self._model_url, temporary)
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise OSError("empty artifact")
            os.replace(temporary, destination)
            return destination, ComponentResult("whisper-model", "acquired")
        except (OSError, PermissionError, urllib.error.URLError):
            return None, ComponentResult("whisper-model", "failed", "make local storage and network access available for the speech model")
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    def _external_runtime(self, component: str, executable: str) -> ComponentResult:
        if self._which_file(executable):
            return ComponentResult(component, "retained")
        acquired = self._platform.acquire_external_runtime(component, self._runner)
        if not acquired.acquired:
            return ComponentResult(component, "unsupported" if acquired.remediation == "unsupported local runtime acquisition" else "failed", acquired.remediation)
        if not self._which_file(executable):
            return ComponentResult(component, "failed", "local runtime was not available after installation")
        return ComponentResult(component, "acquired")

    def _ollama_model(self, preferences: Preferences) -> ComponentResult:
        if self._ollama_ready(preferences.ollama_endpoint, preferences.ollama_model):
            return ComponentResult("ollama-model", "retained")
        if not self._runner(("ollama", "pull", preferences.ollama_model or DEFAULT_OLLAMA_MODEL)):
            return ComponentResult("ollama-model", "failed", "start local Ollama and make network access available for the cleanup model")
        if not self._ollama_ready(preferences.ollama_endpoint, preferences.ollama_model):
            return ComponentResult("ollama-model", "failed", "start local Ollama and verify the cleanup model")
        return ComponentResult("ollama-model", "acquired")

    def _usable_file(self, value: str | None) -> Path | None:
        if not value:
            return None
        path = Path(value)
        return path if path.is_file() and path.stat().st_size > 0 else None

    def _which_file(self, executable: str) -> Path | None:
        value = self._executable_finder(executable)
        return self._usable_file(value)

    @staticmethod
    def _find_executable(executable: str) -> str | None:
        return shutil.which(executable)

    @staticmethod
    def _run(command: Sequence[str]) -> bool:
        try:
            return subprocess.run(tuple(command), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0
        except OSError:
            return False

    @staticmethod
    def _download(url: str, destination: Path) -> None:
        with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)

    @staticmethod
    def _package_is_ready(requirement: str) -> bool:
        name, _, expected = requirement.partition("==")
        try:
            return importlib.metadata.version(name) == expected
        except importlib.metadata.PackageNotFoundError:
            return False

    @staticmethod
    def _ollama_is_ready(endpoint: str, model: str) -> bool:
        try:
            return OllamaClient(endpoint, model).ready()
        except Exception:
            return False



