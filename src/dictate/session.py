"""Ephemeral, single-session dictation state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SessionState(StrEnum):
    IDLE = "idle"
    RECORDING = "recording"
    RECOGNIZING = "recognizing"
    CLEANING = "cleaning"
    VALIDATING_TARGET = "validating-target"
    INSERTED = "inserted"
    RECOVERY = "recovery"
    FAILED = "failed"


_TERMINAL = frozenset({SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED})
_ALLOWED = {
    SessionState.IDLE: {SessionState.RECORDING},
    SessionState.RECORDING: {SessionState.RECOGNIZING, SessionState.FAILED},
    SessionState.RECOGNIZING: {SessionState.CLEANING, SessionState.FAILED},
    SessionState.CLEANING: {SessionState.VALIDATING_TARGET, SessionState.FAILED},
    SessionState.VALIDATING_TARGET: {SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED},
}


@dataclass
class DictationSession:
    state: SessionState = SessionState.IDLE
    audio: bytes | None = None
    transcript: str | None = None
    context: str | None = None
    prompt: str | None = None
    output: str | None = None

    def transition(self, next_state: SessionState) -> None:
        if next_state not in _ALLOWED.get(self.state, set()):
            raise ValueError(f"cannot transition from {self.state} to {next_state}")
        self.state = next_state
        if next_state in _TERMINAL:
            self.clear_content()

    def fail(self) -> None:
        if self.state in _TERMINAL or self.state is SessionState.IDLE:
            raise ValueError(f"cannot fail from {self.state}")
        self.state = SessionState.FAILED
        self.clear_content()

    def reset(self) -> None:
        """Clear a completed session so the next trigger can begin a new one."""
        if self.state not in _TERMINAL and self.state is not SessionState.IDLE:
            raise ValueError(f"cannot reset an active session from {self.state}")
        self.clear_content()
        self.state = SessionState.IDLE

    def clear_content(self) -> None:
        self.audio = self.transcript = self.context = self.prompt = self.output = None

