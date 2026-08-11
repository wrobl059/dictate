from __future__ import annotations

import unittest

from dictate.config import Preferences
from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
from dictate.service import DictationService, PlacementTiming, RecoveryStore


class Clock:
    def __init__(self, values: list[float]) -> None:
        self.values = iter(values)

    def __call__(self) -> float:
        return next(self.values)


class Platform(PlatformAdapter):
    def microphone_permission(self) -> Capability: return Capability(True)
    def trigger_permission(self) -> Capability: return Capability(True)
    def placement_permission(self) -> Capability: return Capability(True)
    def context_permission(self) -> Capability: return Capability(False)
    def snapshot_target(self) -> TargetSnapshot | None: return TargetSnapshot("application", "window", "field")
    def read_context(self, target: TargetSnapshot, limit: int) -> str | None: return None
    def target_matches(self, target: TargetSnapshot) -> bool: return True
    def insert_text(self, target: TargetSnapshot, text: str) -> bool: return True
    def start_hotkey(self, trigger: str, on_press: object, on_release: object) -> None: pass
    def stop_hotkey(self) -> None: pass
    def recovery_instruction(self) -> str: return "dictate serve --recover"


class Recorder:
    def start(self) -> None: pass
    def stop(self) -> bytes: return b"\x00\x00" * 1_600
    def discard(self) -> None: pass


class ASR:
    def start(self) -> None: pass
    def stop(self) -> None: pass
    def transcribe(self, pcm: bytes, terms: tuple[str, ...] = ()) -> str: return "fixed fixture"


class Cleanup:
    def clean(self, transcript: str, style: str, terms: tuple[str, ...] = (), context: str | None = None) -> str: return "fixed fixture"


class LatencyAcceptanceTests(unittest.TestCase):
    def test_warmed_fixed_short_audio_reports_release_to_placement_without_content(self) -> None:
        reports: list[PlacementTiming] = []
        service = DictationService(
            Preferences(), Platform(), Recorder(), ASR(), Cleanup(), recovery=RecoveryStore(),
            clock=Clock([10.0, 14.999]), timing_reporter=reports.append,
        )

        service.press()
        service.release()

        self.assertEqual([PlacementTiming(4_999, "inserted")], reports)
        self.assertTrue(reports[0].meets_five_second_target)
        self.assertFalse(PlacementTiming(5_001, "inserted").meets_five_second_target)
        self.assertFalse(PlacementTiming(1, "recovery-required").meets_five_second_target)
        self.assertFalse(any(hasattr(reports[0], field) for field in ("audio", "transcript", "context", "prompt", "output")))


if __name__ == "__main__":
    unittest.main()

