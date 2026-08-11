from __future__ import annotations

import unittest

from dictate.config import Preferences
from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
from dictate.service import DictationService, RecoveryStore


PLATFORMS = ("macos", "windows", "linux")


class MatrixPlatform(PlatformAdapter):
    """Deterministic platform seam shared by every acceptance-matrix row."""

    def __init__(self) -> None:
        self.active_target = TargetSnapshot("application", "window-a", "field")
        self.writes: list[TargetSnapshot] = []
        self.callbacks: tuple[object, object] | None = None

    def microphone_permission(self) -> Capability: return Capability(True)
    def trigger_permission(self) -> Capability: return Capability(True)
    def placement_permission(self) -> Capability: return Capability(True)
    def context_permission(self) -> Capability: return Capability(False, "grant platform accessibility permission")
    def snapshot_target(self) -> TargetSnapshot | None: return self.active_target
    def read_context(self, target: TargetSnapshot, limit: int) -> str | None: return None
    def target_matches(self, target: TargetSnapshot) -> bool: return target == self.active_target
    def insert_text(self, target: TargetSnapshot, text: str) -> bool:
        if not self.target_matches(target):
            return False
        self.writes.append(target)
        return True
    def start_hotkey(self, trigger: str, on_press: object, on_release: object) -> None: self.callbacks = (on_press, on_release)
    def stop_hotkey(self) -> None: self.callbacks = None
    def recovery_instruction(self) -> str: return "dictate serve --recover"


class Recorder:
    def start(self) -> None: pass
    def stop(self) -> bytes: return FIXED_SHORT_PCM
    def discard(self) -> None: pass


class ASR:
    def start(self) -> None: pass
    def stop(self) -> None: pass
    def transcribe(self, pcm: bytes, terms: tuple[str, ...] = ()) -> str: return "fixture"


class Cleanup:
    def clean(self, transcript: str, style: str, terms: tuple[str, ...] = (), context: str | None = None) -> str: return "fixture"


# 100 ms of deterministic 16 kHz mono signed-16-bit silence, never user audio.
FIXED_SHORT_PCM = b"\x00\x00" * 1_600


class PlatformMatrixAcceptanceTests(unittest.TestCase):
    def test_shared_contract_preserves_trigger_optional_context_and_safe_placement(self) -> None:
        for platform_name in PLATFORMS:
            with self.subTest(platform=platform_name):
                platform = MatrixPlatform()
                recovery = RecoveryStore()
                service = DictationService(Preferences(), platform, Recorder(), ASR(), Cleanup(), recovery=recovery)

                service.start()
                self.assertIsNotNone(platform.callbacks)
                self.assertFalse(platform.context_permission().available)
                self.assertEqual("dictate serve --recover", platform.recovery_instruction())

                service.press()
                platform.active_target = TargetSnapshot("application", "window-b", "field")
                service.release()

                self.assertEqual([], platform.writes)
                self.assertEqual("fixture", recovery.take())
                service.stop()


if __name__ == "__main__":
    unittest.main()

