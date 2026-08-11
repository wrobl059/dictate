from __future__ import annotations

import unittest

from dictate.config import Preferences
from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
from dictate.service import DictationService, RecoveryStore


class FocusPlatform(PlatformAdapter):
    def __init__(self) -> None:
        self.active = TargetSnapshot("app", "A", "field")
        self.writes: list[tuple[str, str]] = []
    def microphone_permission(self) -> Capability: return Capability(True)
    def trigger_permission(self) -> Capability: return Capability(True)
    def placement_permission(self) -> Capability: return Capability(True)
    def context_permission(self) -> Capability: return Capability(False)
    def snapshot_target(self) -> TargetSnapshot | None: return self.active
    def read_context(self, target: TargetSnapshot, limit: int) -> str | None: return None
    def target_matches(self, target: TargetSnapshot) -> bool: return target == self.active
    def insert_text(self, target: TargetSnapshot, text: str) -> bool:
        if target != self.active: return False
        self.writes.append((target.window_id, text)); return True
    def start_hotkey(self, *args: object) -> None: pass
    def stop_hotkey(self) -> None: pass
    def recovery_instruction(self) -> str: return "recover"


class Recorder:
    def start(self) -> None: pass
    def stop(self) -> bytes: return b"pcm"
    def discard(self) -> None: pass
class ASR:
    def start(self) -> None: pass
    def stop(self) -> None: pass
    def transcribe(self, pcm: bytes, terms: tuple[str, ...] = ()) -> str: return "spoken"
class Cleanup:
    def clean(self, transcript: str, style: str, terms: tuple[str, ...] = (), context: object = None) -> str: return "polished"


class FocusSafetyAcceptanceTests(unittest.TestCase):
    def test_focus_change_from_a_to_b_never_writes_to_b_and_requires_recovery(self) -> None:
        platform, recovery = FocusPlatform(), RecoveryStore()
        service = DictationService(Preferences(), platform, Recorder(), ASR(), Cleanup(), recovery=recovery)
        service.press()
        platform.active = TargetSnapshot("app", "B", "field")
        service.release()
        self.assertEqual([], platform.writes)
        self.assertEqual("polished", recovery.take())


if __name__ == "__main__":
    unittest.main()

