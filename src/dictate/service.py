"""Content-free readiness checks and the safe local dictation orchestration."""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from dictate.config import Preferences
from dictate.context import BoundedContext
from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
from dictate.privacy import PrivacyError, validate_loopback_url
from dictate.session import DictationSession, SessionState


class ReadinessBoundary(Protocol):
    def asr_ready(self, endpoint: str) -> Capability: ...
    def ollama_model_ready(self, endpoint: str, model: str) -> Capability: ...
    def microphone_ready(self, device: str) -> Capability: ...
    def trigger_ready(self, trigger: str) -> Capability: ...
    def placement_ready(self) -> Capability: ...
    def context_ready(self) -> Capability: ...


@dataclass(frozen=True)
class ReadinessResult:
    required_failures: tuple[str, ...]
    limitations: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.required_failures


@dataclass(frozen=True)
class PlacementTiming:
    """Content-free timing from trigger release to terminal placement outcome."""

    duration_ms: int
    outcome: str

    @property
    def meets_five_second_target(self) -> bool:
        return self.outcome == "inserted" and self.duration_ms <= 5_000


def check_readiness(preferences: Preferences, boundary: ReadinessBoundary) -> ReadinessResult:
    """Check every required local capability without collecting user content."""
    try:
        validate_loopback_url(preferences.asr_endpoint)
        validate_loopback_url(preferences.ollama_endpoint)
    except PrivacyError as error:
        return ReadinessResult((str(error),), ())
    required = (
        ("local ASR", boundary.asr_ready(preferences.asr_endpoint)),
        ("local Ollama model", boundary.ollama_model_ready(preferences.ollama_endpoint, preferences.ollama_model)),
        ("microphone", boundary.microphone_ready(preferences.microphone)),
        ("global trigger", boundary.trigger_ready(preferences.trigger)),
        ("safe text placement", boundary.placement_ready()),
    )
    failures = tuple(f"{name}: {value.remediation or 'unavailable'}" for name, value in required if not value.available)
    context = boundary.context_ready()
    limitations = () if context.available else (f"destination context: {context.remediation or 'unavailable'}",)
    return ReadinessResult(failures, limitations)


class RecorderBoundary(Protocol):
    def start(self) -> None: ...
    def stop(self) -> bytes: ...
    def discard(self) -> None: ...


class ASRBoundary(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def transcribe(self, pcm: bytes, terms: Sequence[str] = ()) -> str: ...


class CleanupBoundary(Protocol):
    def clean(self, transcript: str, style: str, terms: Sequence[str] = (), context: str | None = None) -> str: ...


class RecoveryStore:
    """One process-local result, destructively read and never persisted."""

    def __init__(self, timeout_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic) -> None:
        self._timeout_seconds = timeout_seconds
        self._clock = clock
        self._result: str | None = None
        self._expires_at: float | None = None

    def put(self, result: str) -> None:
        self.clear()
        self._result = result
        self._expires_at = self._clock() + self._timeout_seconds

    def take(self) -> str | None:
        if self._expires_at is None or self._clock() >= self._expires_at:
            self.clear()
            return None
        result = self._result
        self.clear()
        return result

    def clear(self) -> None:
        self._result = None
        self._expires_at = None


DEFAULT_RECOVERY = RecoveryStore()


class DictationService:
    """One active session: snapshot → RAM audio → ASR → Ollama → safe insert/recovery."""

    def __init__(
        self,
        preferences: Preferences,
        platform: PlatformAdapter,
        recorder: RecorderBoundary,
        asr: ASRBoundary,
        cleanup: CleanupBoundary,
        *,
        recovery: RecoveryStore = DEFAULT_RECOVERY,
        status: Callable[[str], None] | None = None,
        terms_for_target: Callable[[TargetSnapshot], Sequence[str]] | None = None,
        clock: Callable[[], float] = time.monotonic,
        timing_reporter: Callable[[PlacementTiming], None] | None = None,
    ) -> None:
        self.preferences = preferences
        self.platform = platform
        self.recorder = recorder
        self.asr = asr
        self.cleanup = cleanup
        self.recovery = recovery
        self.status = status or (lambda _event: None)
        self.terms_for_target = terms_for_target or (lambda _target: ())
        self._clock = clock
        self._timing_reporter = timing_reporter or (lambda _timing: None)
        self.session = DictationSession()
        self._target: TargetSnapshot | None = None
        self._terms: tuple[str, ...] = ()

    def start(self) -> None:
        self.asr.start()
        self.platform.start_hotkey(self.preferences.trigger, self.press, self.release)

    def stop(self) -> None:
        try:
            self.platform.stop_hotkey()
        finally:
            try:
                if self.session.state is SessionState.RECORDING:
                    try:
                        self.recorder.stop()
                    except Exception:
                        pass
                    finally:
                        self.recorder.discard()
                elif self.session.state not in (SessionState.IDLE, SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED):
                    self.recorder.discard()
            finally:
                try:
                    self.asr.stop()
                finally:
                    self.recovery.clear()
                    self._target = None
                    if self.session.state not in (SessionState.IDLE, SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED):
                        self.session.fail()
                    if self.session.state is not SessionState.IDLE:
                        self.session.reset()

    def press(self) -> None:
        if self.session.state is not SessionState.IDLE:
            self.status("dictation-busy")
            return
        target = self.platform.snapshot_target()
        if target is None:
            self.status("target-unavailable")
            return
        try:
            self._target = target
            self._terms = tuple(self.terms_for_target(target))
            context_permission = getattr(self.platform, "context_permission", lambda: Capability(False))()
            if context_permission.available:
                try:
                    raw_context = self.platform.read_context(target, self.preferences.context_limit)
                    self.session.context = raw_context.render(self.preferences.context_limit) if isinstance(raw_context, BoundedContext) else (raw_context or "")[:self.preferences.context_limit] or None
                except Exception:
                    self.session.context = None
            self.session.transition(SessionState.RECORDING)
            self.recorder.start()
        except Exception:
            self._fail("recording-unavailable")

    def release(self) -> None:
        if self.session.state is not SessionState.RECORDING:
            return
        released_at = self._clock()
        outcome = "local-processing-failed"
        try:
            audio = self.recorder.stop()
            self.session.audio = audio
            if not audio:
                self._fail("empty-capture")
                outcome = "empty-capture"
                return
            self.session.transition(SessionState.RECOGNIZING)
            transcript = self.asr.transcribe(audio, terms=self._terms)
            self.session.transcript = transcript
            self.session.transition(SessionState.CLEANING)
            output = self.cleanup.clean(transcript, self.preferences.style, terms=self._terms, context=self.session.context)
            if not isinstance(output, str) or not output.strip():
                raise ValueError("local cleanup returned no usable output")
            self.session.output = output
            self.session.transition(SessionState.VALIDATING_TARGET)
            target = self._target
            if target is None or not self.platform.target_matches(target) or not self.platform.insert_text(target, output):
                self.recovery.put(output)
                self.session.transition(SessionState.RECOVERY)
                self.status("recovery-required")
                outcome = "recovery-required"
                return
            self.session.transition(SessionState.INSERTED)
            self.status("inserted")
            outcome = "inserted"
        except Exception:
            self._fail("local-processing-failed")
        finally:
            duration_ms = max(0, round((self._clock() - released_at) * 1_000))
            self._timing_reporter(PlacementTiming(duration_ms, outcome))
            self._target = None
            self._terms = ()
            if self.session.state in (SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED):
                self.session.reset()

    def _fail(self, event: str) -> None:
        try:
            self.recorder.discard()
        except Exception:
            pass
        if self.session.state not in (SessionState.IDLE, SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED):
            self.session.fail()
        if self.session.state is not SessionState.IDLE:
            self.session.reset()
        self._target = None
        self._terms = ()
        self.status(event)


