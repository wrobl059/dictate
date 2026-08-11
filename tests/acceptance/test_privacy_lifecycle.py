from __future__ import annotations

import io
import logging
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from dictate.cleanup import OllamaClient
from dictate.config import Preferences, save_preferences
from dictate.platform.base import TargetSnapshot
from dictate.privacy import PrivacyError, log_metadata
from dictate.service import DictationService, RecoveryStore
from dictate.session import SessionState


class Recorder:
    def __init__(self, audio: bytes) -> None:
        self.audio = audio
        self.stopped = False
        self.discarded = False
    def start(self) -> None: pass
    def stop(self) -> bytes:
        self.stopped = True
        return self.audio
    def discard(self) -> None:
        self.audio = b""
        self.discarded = True


class PrivacyLifecycleAcceptanceTests(unittest.TestCase):
    def platform(self, *, insert: bool = True) -> tuple[SimpleNamespace, list[str]]:
        writes: list[str] = []
        target = TargetSnapshot("app", "window", "field")
        return SimpleNamespace(
            snapshot_target=lambda: target,
            target_matches=lambda value: value == target,
            insert_text=lambda value, text: writes.append(text) is None and insert,
            start_hotkey=lambda *args: None,
            stop_hotkey=lambda: None,
        ), writes

    def test_content_sentinels_do_not_persist_after_success_or_recovery_read(self) -> None:
        markers = ("AUDIO-SENTINEL", "TRANSCRIPT-SENTINEL", "CONTEXT-SENTINEL", "PROMPT-SENTINEL", "OUTPUT-SENTINEL", "RECOVERY-SENTINEL")
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "preferences.toml"
            save_preferences(config, Preferences())
            class ProbeCleanup(OllamaClient):
                def __init__(self) -> None:
                    super().__init__("http://127.0.0.1:11434", "qwen3:4b-instruct-2507-q4_K_M")
                    self.payload: dict[str, object] | None = None
                def _request(self, payload: dict[str, object]) -> dict[str, object]:
                    self.payload = payload
                    return {"response": markers[4]}
            probe = ProbeCleanup()
            self.assertEqual(markers[4], probe.clean(markers[1], "Natural", [markers[2]], f"{markers[3]} {markers[3]}"))
            self.assertIn(markers[1], probe.payload["prompt"])
            self.assertIn(markers[2], probe.payload["prompt"])
            self.assertIn(markers[3], probe.payload["prompt"])
            probe.payload = None
            platform, writes = self.platform()
            recorder = Recorder(markers[0].encode())
            asr = SimpleNamespace(start=lambda: None, stop=lambda: None, transcribe=lambda pcm, terms=(): markers[1])
            cleanup = SimpleNamespace(clean=lambda transcript, style, terms=(), context=None: markers[4])
            service = DictationService(Preferences(), platform, recorder, asr, cleanup, recovery=RecoveryStore())
            service.press(); service.release()
            self.assertEqual([markers[4] + " "], writes)
            self.assertEqual(SessionState.IDLE, service.session.state)
            self.assertTrue(all(getattr(service.session, field) is None for field in ("audio", "transcript", "context", "prompt", "output")))
            persisted = "".join(path.read_text(encoding="utf-8", errors="ignore") for path in Path(directory).rglob("*") if path.is_file())
            self.assertTrue(all(marker not in persisted for marker in markers))
        recovery = RecoveryStore()
        recovery.put(markers[5])
        self.assertEqual(markers[5], recovery.take())
        self.assertIsNone(recovery.take())

    def test_cancellation_closes_and_discards_recording_content(self) -> None:
        platform, _ = self.platform()
        recorder = Recorder(b"AUDIO-SENTINEL")
        service = DictationService(Preferences(), platform, recorder, SimpleNamespace(start=lambda: None, stop=lambda: None), SimpleNamespace(), recovery=RecoveryStore())
        service.press()
        service.stop()
        self.assertTrue(recorder.stopped)
        self.assertTrue(recorder.discarded)
        self.assertEqual(b"", recorder.audio)
        self.assertEqual(SessionState.IDLE, service.session.state)

    def test_logging_rejects_content_in_event_and_error(self) -> None:
        logger = logging.getLogger("dictate-privacy-lifecycle")
        logger.handlers[:] = [logging.StreamHandler(io.StringIO())]
        with self.assertRaises(PrivacyError):
            log_metadata(logger, "TRANSCRIPT-SENTINEL")
        with self.assertRaises(PrivacyError):
            log_metadata(logger, "ready", {"error": "TRANSCRIPT-SENTINEL"})


if __name__ == "__main__":
    unittest.main()


