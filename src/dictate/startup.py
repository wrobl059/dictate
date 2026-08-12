"""Foreground supervision for Dictate and its locally installed dependencies."""

from __future__ import annotations

import os
import shutil
import sys
import time
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from dictate.asr import ASRError, WhisperServer, whisper_server_command
from dictate.audio import Recorder
from dictate.cleanup import CleanupError, OllamaClient, OllamaServer
from dictate.config import Preferences
from dictate.dictionary import global_dictionary_path, terms_for_paths
from dictate.platform.base import PlatformAdapter, TargetSnapshot
from dictate.readiness import LocalReadiness
from dictate.service import DictationService, check_readiness

READY_TIMEOUT_SECONDS = 30.0


class ManagedDependency(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def running(self) -> bool: ...


class RuntimeLock:
    """A content-free, invocation-scoped lock; it never identifies user data."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.owner = uuid.uuid4().hex
        self._held = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return False
        with os.fdopen(descriptor, "w", encoding="ascii") as file:
            file.write(self.owner)
        self._held = True
        return True

    def release(self) -> None:
        if not self._held:
            return
        try:
            if self.path.read_text(encoding="ascii") == self.owner:
                self.path.unlink(missing_ok=True)
        except OSError:
            pass
        finally:
            self._held = False


class _ASRFacade:
    """Inference-only ASR view so DictationService cannot own a dependency process."""

    def __init__(self, client: WhisperServer) -> None:
        self._client = client

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def transcribe(self, pcm: bytes, terms: Sequence[str] = ()) -> str:
        return self._client.transcribe(pcm, terms)


class CombinedStartup:
    """Coordinate one safe, local-only Dictate foreground invocation."""

    def __init__(
        self,
        preferences: Preferences,
        platform: PlatformAdapter,
        *,
        status: Callable[[str], None] | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        lock: RuntimeLock | None = None,
        asr_factory: Callable[[str, Sequence[str] | None], WhisperServer] | None = None,
        ollama_factory: Callable[[str], OllamaServer] | None = None,
        service_factory: Callable[..., DictationService] = DictationService,
    ) -> None:
        self.preferences = preferences
        self.platform = platform
        self._status = status or (lambda message: print(message, file=sys.stderr))
        self._clock = clock
        self._sleep = sleep
        self._lock = lock or RuntimeLock(Path.home() / ".config" / "dictate" / "runtime.lock")
        self._asr_factory = asr_factory or (lambda endpoint, command: WhisperServer(endpoint, command))
        self._ollama_factory = ollama_factory or (lambda endpoint: OllamaServer(endpoint))
        self._service_factory = service_factory
        self._service: DictationService | None = None
        self._owned: list[ManagedDependency] = []

    def run(self) -> int:
        """Run until interrupted; all lifecycle messages are fixed and content-free."""
        try:
            if not self._lock.acquire():
                self._status("Dictate is already running")
                return 1
            return self._run_locked()
        finally:
            self._cleanup()
            self._lock.release()

    def _run_locked(self) -> int:
        try:
            asr_client = WhisperServer(self.preferences.asr_endpoint)
            cleanup_client = OllamaClient(self.preferences.ollama_endpoint, self.preferences.ollama_model)
        except Exception:
            self._status("dictate: unsafe local dependency endpoint")
            return 1

        asr_ready = asr_client.ready()
        cleanup_ready = cleanup_client.ready()
        try:
            if not asr_ready:
                command = whisper_server_command(self.preferences)
                asr_server = self._asr_factory(self.preferences.asr_endpoint, command)
                asr_server.start()
                self._owned.append(asr_server)
            if not cleanup_ready:
                if shutil.which("ollama") is None:
                    raise CleanupError("local Ollama runtime must be installed")
                ollama_server = self._ollama_factory(self.preferences.ollama_endpoint)
                ollama_server.start()
                self._owned.append(ollama_server)
        except (ASRError, CleanupError, OSError):
            self._status("dictate: local dependency is unavailable; run dictate setup --install-dependencies")
            return 1

        deadline = self._clock() + READY_TIMEOUT_SECONDS
        result = None
        while self._clock() <= deadline:
            try:
                result = check_readiness(self.preferences, LocalReadiness(self.platform))
            except Exception:
                result = None
            if result is not None and result.ready:
                break
            self._sleep(0.1)
        if result is None or not result.ready:
            if result is not None:
                for failure in result.required_failures:
                    self._status(f"dictate: not ready: {failure}")
                if any(failure.startswith(("local ASR:", "local Ollama model:")) for failure in result.required_failures):
                    self._status("dictate: run dictate setup --install-dependencies to acquire missing local components")
            else:
                self._status("dictate: local dependencies or permissions are not ready")
            return 1

        try:
            global_terms = terms_for_paths(global_dictionary_path())
            self._service = self._service_factory(
                self.preferences,
                self.platform,
                Recorder(self.preferences.microphone),
                _ASRFacade(asr_client),
                cleanup_client,
                status=lambda event: self._status(f"dictate: {event}"),
                terms_for_target=lambda _target: global_terms,
            )
            self._service.start()
        except Exception:
            self._status("dictate: could not start local dictation service")
            return 1
        self._status("dictate: ready")
        try:
            while True:
                if any(not dependency.running() for dependency in self._owned):
                    self._status("dictate: local dependency stopped; shutting down")
                    return 1
                self._sleep(0.2)
        except KeyboardInterrupt:
            return 0

    def _cleanup(self) -> None:
        if self._service is not None:
            try:
                self._service.stop()
            except Exception:
                pass
            self._service = None
        while self._owned:
            try:
                self._owned.pop().stop()
            except Exception:
                pass
