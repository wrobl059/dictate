"""Concrete, content-free readiness checks for the local runtime boundaries."""

from __future__ import annotations

from collections.abc import Callable

from dictate.asr import WhisperServer
from dictate.audio import AudioInputDevice, list_input_devices, microphone_available
from dictate.cleanup import OllamaClient
from dictate.platform.base import Capability, PlatformAdapter


class LocalReadiness:
    """Check installed local capabilities without recording or handling user content."""

    def __init__(
        self,
        platform: PlatformAdapter,
        *,
        devices: Callable[[], tuple[AudioInputDevice, ...]] = list_input_devices,
        asr_factory: Callable[[str], WhisperServer] = WhisperServer,
        cleanup_factory: Callable[[str, str], OllamaClient] = OllamaClient,
    ) -> None:
        self._platform = platform
        self._devices = devices
        self._asr_factory = asr_factory
        self._cleanup_factory = cleanup_factory

    def asr_ready(self, endpoint: str) -> Capability:
        try:
            available = self._asr_factory(endpoint).ready()
        except Exception:
            available = False
        return Capability(available, None if available else "start the local whisper.cpp server and verify its loopback endpoint")

    def ollama_model_ready(self, endpoint: str, model: str) -> Capability:
        try:
            available = self._cleanup_factory(endpoint, model).ready()
        except Exception:
            available = False
        return Capability(available, None if available else "start local Ollama and acquire the configured model")

    def microphone_ready(self, device: str) -> Capability:
        permission = self._platform.microphone_permission()
        if not permission.available:
            return permission
        try:
            available = microphone_available(device, self._devices())
        except Exception:
            available = False
        return Capability(available, None if available else "connect or select an available microphone")

    def trigger_ready(self, trigger: str) -> Capability:
        return self._platform.trigger_permission()

    def placement_ready(self) -> Capability:
        return self._platform.placement_permission()

    def context_ready(self) -> Capability:
        return self._platform.context_permission()

