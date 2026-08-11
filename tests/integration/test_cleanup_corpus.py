from __future__ import annotations

import json
import unittest
from pathlib import Path

from dictate.cleanup import OllamaClient


class CorpusClient(OllamaClient):
    def __init__(self, response: str) -> None:
        super().__init__("http://127.0.0.1:11434", "qwen3:4b-instruct-2507-q4_K_M")
        self.response = response
        self.payload: dict[str, object] | None = None

    def _request(self, payload: dict[str, object]) -> dict[str, object]:
        self.payload = payload
        return {"response": self.response}


class CleanupCorpusIntegrationTests(unittest.TestCase):
    def test_fixed_corpus_preserves_expected_transformation_for_every_style(self) -> None:
        corpus_path = Path(__file__).parents[1] / "fixtures" / "cleanup-corpus.json"
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        self.assertEqual({"Natural", "Formal", "Casual", "Technical"}, {case["style"] for case in corpus})
        for case in corpus:
            with self.subTest(case=case["id"]):
                client = CorpusClient(case["expected"])
                result = client.clean(case["transcript"], case["style"], case["terms"], case["context"])
                self.assertEqual(case["expected"], result)
                assert client.payload is not None
                self.assertFalse(client.payload["stream"])
                self.assertFalse(client.payload["think"])
                self.assertEqual(0, client.payload["options"]["temperature"])
                self.assertEqual(2048, client.payload["options"]["num_ctx"])
                prompt = client.payload["prompt"]
                self.assertIn(f"Style: {case['style']}", prompt)
                self.assertIn(f"Transcript: {case['transcript']}", prompt)
                self.assertIn("preserving its intended meaning, substantive wording, emphasis", prompt)
                self.assertIn("Remove conversational filler, hesitations, repetitions, and abandoned phrasing", prompt)
                self.assertIn("Do not paraphrase, substitute synonyms, summarize, infer unstated intent", prompt)
                for term in case["terms"]:
                    self.assertIn(term, prompt)
                if case["context"]:
                    self.assertIn(case["context"], prompt)


if __name__ == "__main__":
    unittest.main()

