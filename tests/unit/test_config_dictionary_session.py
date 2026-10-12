from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dictate.config import Preferences, load_preferences, save_preferences
from dictate.dictionary import add_dictionary_term, load_dictionary, merge_dictionaries, remove_dictionary_term
from dictate.session import DictationSession, SessionState


class ConfigDictionarySessionTests(unittest.TestCase):
    def test_defaults_use_natural_system_microphone_and_blessed_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            preferences = load_preferences(Path(directory) / "missing.toml")
        self.assertEqual("Natural", preferences.style)
        self.assertEqual("system-default", preferences.microphone)
        self.assertEqual("right_alt", preferences.trigger)

    def test_preferences_are_written_as_readable_toml_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.toml"
            saved = Preferences(style="Technical", microphone="device-1")
            save_preferences(path, saved)
            self.assertEqual(saved, load_preferences(path))
            self.assertFalse(list(Path(directory).glob(".preferences.toml.*")))

    def test_verified_whisper_locations_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "preferences.toml"
            saved = Preferences(whisper_server_executable=str(root / "whisper-server"), whisper_model_path=str(root / "ggml-base.bin"))
            save_preferences(path, saved)
            self.assertEqual(saved, load_preferences(path))

    def test_relative_whisper_location_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "absolute local path"):
            save_preferences(Path(tempfile.gettempdir()) / "dictate-invalid.toml", Preferences(whisper_model_path="relative-model.bin"))

    def test_project_dictionary_overrides_global_spelling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dictionary.txt"
            path.write_text("Ollama\nDictate\n", encoding="utf-8")
            global_terms = load_dictionary(path)
        self.assertEqual(("Dictate", "OLLAMA"), merge_dictionaries(global_terms, {"ollama": "OLLAMA"}))

    def test_duplicate_dictionary_term_reports_local_line_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dictionary.txt"
            path.write_text("Ollama\nOLLAMA\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lines 1 and 2"):
                load_dictionary(path)

    def test_dictionary_edits_are_atomic_and_preserve_original_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "dictionary.txt"
            path.write_text("Ollama\nDictate\n", encoding="utf-8")
            add_dictionary_term(path, "GitHub")
            self.assertTrue(remove_dictionary_term(path, "ollama"))
            self.assertEqual("Dictate\nGitHub\n", path.read_text(encoding="utf-8"))
            self.assertFalse(list(root.glob(".dictionary.txt.*")))

    def test_dictionary_add_rejects_terms_that_would_be_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dictionary.txt"
            with self.assertRaisesRegex(ValueError, "at most 120"):
                add_dictionary_term(path, "a" * 121)

    def test_every_terminal_state_clears_content(self) -> None:
        for terminal in (SessionState.INSERTED, SessionState.RECOVERY, SessionState.FAILED):
            with self.subTest(terminal=terminal):
                session = DictationSession(
                    state=SessionState.VALIDATING_TARGET,
                    audio=b"audio",
                    transcript="transcript",
                    context="context",
                    prompt="prompt",
                    output="output",
                )
                session.transition(terminal)
                self.assertEqual(terminal, session.state)
                self.assertEqual((None, None, None, None, None), (session.audio, session.transcript, session.context, session.prompt, session.output))

    def test_failure_clears_content(self) -> None:
        session = DictationSession(state=SessionState.RECORDING, audio=b"audio", transcript="transcript")
        session.fail()
        self.assertEqual(SessionState.FAILED, session.state)
        self.assertIsNone(session.audio)
        self.assertIsNone(session.transcript)


if __name__ == "__main__":
    unittest.main()

