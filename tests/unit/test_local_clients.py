from __future__ import annotations

import unittest

from dictate.cleanup import OllamaServer


class Process:
    def __init__(self) -> None:
        self.terminated = False

    def poll(self) -> int | None:
        return 0 if self.terminated else None

    def terminate(self) -> None:
        self.terminated = True


class LocalProcessTests(unittest.TestCase):
    def test_ollama_server_starts_and_stops_only_its_injected_process(self) -> None:
        process = Process()
        commands: list[tuple[str, ...]] = []

        def popen(command: tuple[str, ...], **_kwargs: object) -> Process:
            commands.append(command)
            return process

        server = OllamaServer("http://127.0.0.1:11434", popen=popen)  # type: ignore[arg-type]
        server.start()
        self.assertEqual([("ollama", "serve")], commands)
        self.assertTrue(server.running())
        server.stop()
        server.stop()
        self.assertTrue(process.terminated)
        self.assertFalse(server.running())


if __name__ == "__main__":
    unittest.main()

