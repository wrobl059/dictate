from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dictate.config import Preferences, load_preferences, save_preferences
from dictate.dictionary import load_dictionary, merge_dictionaries
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

    def test_project_dictionary_overrides_global_spelling(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dictionary.txt"
            path.write_text("Ollama\nDictate\n", encoding="utf-8")
            global_terms = load_dictionary(path)
        self.assertEqual(("Dictate", "OLLAMA"), merge_dictionaries(global_terms, {"ollama": "OLLAMA"}))

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


