from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dictate.audio import AudioInputDevice, microphone_available
from dictate.context import BoundedContext
from dictate.dictionary import terms_for_paths


class DictionaryContextAudioTests(unittest.TestCase):
    def test_project_dictionary_overrides_global_for_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            global_path = root / "global.txt"
            project_path = root / "project" / ".dictate" / "dictionary.txt"
            global_path.write_text("Ollama\nPython\n", encoding="utf-8")
            project_path.parent.mkdir(parents=True)
            project_path.write_text("OLLAMA\nDictate\n", encoding="utf-8")
            self.assertEqual(("Dictate", "OLLAMA", "Python"), terms_for_paths(global_path, root / "project"))

    def test_context_is_limited_to_selection_and_nearby_text(self) -> None:
        self.assertEqual("selected\nnear", BoundedContext("selected", "nearby").render(13))
        self.assertEqual("selec", BoundedContext("selected", "nearby").render(5))

    def test_microphone_selection_is_checked_before_recording(self) -> None:
        devices = (AudioInputDevice("2", "Mic"),)
        self.assertTrue(microphone_available("system-default", devices))
        self.assertTrue(microphone_available("2", devices))
        self.assertFalse(microphone_available("9", devices))
        self.assertFalse(microphone_available("system-default", ()))


if __name__ == "__main__":
    unittest.main()


