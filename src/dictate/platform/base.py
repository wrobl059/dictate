"""The only polymorphic boundary for OS integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    available: bool
    remediation: str | None = None


@dataclass(frozen=True)
class AcquisitionResult:
    """Content-free result from an OS-specific runtime acquisition route."""

    acquired: bool
    remediation: str | None = None


@dataclass(frozen=True)
class TargetSnapshot:
    application_id: str
    window_id: str
    text_target_id: str


class PlatformAdapter(ABC):
    def acquire_external_runtime(
        self, component: str, runner: Callable[[Sequence[str]], bool]
    ) -> AcquisitionResult:
        """Reject acquisition unless a concrete OS adapter provides one explicit route."""
        return AcquisitionResult(False, "unsupported local runtime acquisition")

    @abstractmethod
    def microphone_permission(self) -> Capability: ...

    @abstractmethod
    def trigger_permission(self) -> Capability: ...

    @abstractmethod
    def placement_permission(self) -> Capability: ...

    @abstractmethod
    def context_permission(self) -> Capability: ...

    @abstractmethod
    def snapshot_target(self) -> TargetSnapshot | None: ...

    @abstractmethod
    def read_context(self, target: TargetSnapshot, limit: int) -> str | None: ...

    @abstractmethod
    def target_matches(self, target: TargetSnapshot) -> bool: ...

    @abstractmethod
    def insert_text(self, target: TargetSnapshot, text: str) -> bool: ...


    def release_target(self, target: TargetSnapshot) -> None:
        """Discard any adapter-local native reference retained for a target."""

    @abstractmethod
    def start_hotkey(self, trigger: str, on_press: object, on_release: object) -> None: ...

    @abstractmethod
    def stop_hotkey(self) -> None: ...

    @abstractmethod
    def recovery_instruction(self) -> str: ...

