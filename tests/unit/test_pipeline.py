from __future__ import annotations

import unittest

from dictate.config import Preferences
from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
from dictate.service import DictationService, RecoveryStore
from dictate.session import SessionState


class Platform(PlatformAdapter):
    def __init__(self) -> None:
        self.target = TargetSnapshot("app", "window-a", "field")
        self.matches = True
        self.inserted: list[tuple[TargetSnapshot, str]] = []
        self.released: list[TargetSnapshot] = []
        self.callbacks = None

    def microphone_permission(self) -> Capability: return Capability(True)
    def trigger_permission(self) -> Capability: return Capability(True)
    def placement_permission(self) -> Capability: return Capability(True)
    def context_permission(self) -> Capability: return Capability(False)
    def snapshot_target(self) -> TargetSnapshot | None: return self.target
    def read_context(self, target: TargetSnapshot, limit: int) -> str | None: return None
    def target_matches(self, target: TargetSnapshot) -> bool: return self.matches and target == self.target
    def insert_text(self, target: TargetSnapshot, text: str) -> bool:
        if not self.target_matches(target):
            return False
        self.inserted.append((target, text))
        return True
    def release_target(self, target: TargetSnapshot) -> None: self.released.append(target)
    def start_hotkey(self, trigger: str, on_press: object, on_release: object) -> None: self.callbacks = (on_press, on_release)
    def stop_hotkey(self) -> None: self.callbacks = None
    def recovery_instruction(self) -> str: return "recover"


class Recorder:
    def __init__(self, audio: bytes = b"pcm") -> None:
        self.audio = audio
        self.started = False
        self.stopped = False
        self.discarded = False

    def start(self) -> None: self.started = True
    def stop(self) -> bytes:
        self.stopped = True
        return self.audio
    def discard(self) -> None: self.discarded = True


class ASR:
    def __init__(self, text: str = "spoken words") -> None:
        self.text = text
        self.calls: list[tuple[bytes, tuple[str, ...]]] = []
        self.started = False
    def start(self) -> None: self.started = True
    def stop(self) -> None: pass
    def transcribe(self, pcm: bytes, terms: tuple[str, ...] = ()) -> str:
        self.calls.append((pcm, terms))
        return self.text


class Cleanup:
    def __init__(self, text: str = "Polished words") -> None:
        self.text = text
        self.calls: list[tuple[str, str, tuple[str, ...], object]] = []
    def clean(self, transcript: str, style: str, terms: tuple[str, ...] = (), context: object = None) -> str:
        self.calls.append((transcript, style, terms, context))
        return self.text


class PipelineTests(unittest.TestCase):
    def make_service(self, *, audio: bytes = b"pcm") -> tuple[DictationService, Platform, Recorder, ASR, Cleanup, RecoveryStore]:
        platform, recorder, asr, cleanup, recovery = Platform(), Recorder(audio), ASR(), Cleanup(), RecoveryStore()
        return DictationService(Preferences(), platform, recorder, asr, cleanup, recovery=recovery), platform, recorder, asr, cleanup, recovery

    def test_press_snapshots_then_starts_and_release_runs_mandatory_pipeline(self) -> None:
        service, platform, recorder, asr, cleanup, _ = self.make_service()
        cleanup.text = "Polished words   \n"
        service.press()
        self.assertTrue(recorder.started)
        service.release()
        self.assertTrue(recorder.stopped)
        self.assertEqual([(b"pcm", ())], asr.calls)
        self.assertEqual(("spoken words", "Natural", (), None), cleanup.calls[0])
        self.assertEqual([(platform.target, "Polished words ")], platform.inserted)
        self.assertEqual([platform.target], platform.released)
        self.assertEqual(SessionState.IDLE, service.session.state)

    def test_empty_audio_never_reaches_asr_cleanup_or_insertion(self) -> None:
        service, platform, _, asr, cleanup, _ = self.make_service(audio=b"")
        service.press()
        service.release()
        self.assertEqual([], asr.calls)
        self.assertEqual([], cleanup.calls)
        self.assertEqual([], platform.inserted)
        self.assertEqual([TargetSnapshot("app", "window-a", "field")], platform.released)
        self.assertEqual(SessionState.IDLE, service.session.state)

    def test_target_mismatch_never_injects_and_requires_one_recovery_read(self) -> None:
        service, platform, _, _, _, recovery = self.make_service()
        service.press()
        platform.target = TargetSnapshot("app", "window-b", "field")
        service.release()
        self.assertEqual([], platform.inserted)
        self.assertEqual(SessionState.IDLE, service.session.state)
        self.assertEqual("Polished words ", recovery.take())
        self.assertIsNone(recovery.take())


    def test_asr_or_cleanup_failure_never_inserts(self) -> None:
        for failure in ("asr", "cleanup"):
            with self.subTest(failure=failure):
                platform, recorder, asr, cleanup, recovery = Platform(), Recorder(), ASR(), Cleanup(), RecoveryStore()
                events: list[str] = []
                service = DictationService(Preferences(), platform, recorder, asr, cleanup, recovery=recovery, status=events.append)
                if failure == "asr":
                    asr.transcribe = lambda pcm, terms=(): (_ for _ in ()).throw(RuntimeError("failure"))
                else:
                    cleanup.clean = lambda transcript, style, terms=(), context=None: (_ for _ in ()).throw(RuntimeError("failure"))
                service.press()
                service.release()
                self.assertEqual([], platform.inserted)
                self.assertEqual(SessionState.IDLE, service.session.state)
                self.assertEqual([f"local-processing-failed-{failure}"], events)

    def test_capture_stop_failure_reports_fixed_content_free_stage(self) -> None:
        service, platform, recorder, _, _, _ = self.make_service()
        events: list[str] = []
        service.status = events.append
        recorder.stop = lambda: (_ for _ in ()).throw(RuntimeError("failure"))
        service.press()
        service.release()
        self.assertEqual([], platform.inserted)
        self.assertEqual(["local-processing-failed-capture-stop"], events)

    def test_terminal_outcomes_allow_a_following_dictation(self) -> None:
        service, platform, _, asr, cleanup, _ = self.make_service()
        service.press()
        service.release()
        service.press()
        service.release()
        self.assertEqual(2, len(platform.inserted))
        self.assertEqual(2, len(asr.calls))
        self.assertEqual(2, len(cleanup.calls))
        self.assertEqual(SessionState.IDLE, service.session.state)

    def test_release_without_a_pressed_trigger_does_nothing(self) -> None:
        service, platform, recorder, asr, cleanup, _ = self.make_service()
        service.release()
        self.assertFalse(recorder.started)
        self.assertEqual([], asr.calls)
        self.assertEqual([], cleanup.calls)
        self.assertEqual([], platform.inserted)

    def test_second_press_during_active_dictation_is_rejected_without_duplicate_recording(self) -> None:
        platform, recorder, asr, cleanup, recovery = Platform(), Recorder(), ASR(), Cleanup(), RecoveryStore()
        events: list[str] = []
        service = DictationService(Preferences(), platform, recorder, asr, cleanup, recovery=recovery, status=events.append)
        service.press()
        service.press()
        service.release()
        self.assertEqual(["dictation-busy", "inserted"], events)
        self.assertEqual(1, len(asr.calls))


if __name__ == "__main__":
    unittest.main()


