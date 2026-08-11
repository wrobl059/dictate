from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dictate.asr import WhisperServer
from dictate.cleanup import OllamaClient


class Handler(BaseHTTPRequestHandler):
    requests: list[tuple[str, dict[str, str], bytes]] = []

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers["Content-Length"]))
        type(self).requests.append((self.path, dict(self.headers), body))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.path == "/inference":
            self.wfile.write(b'{"text":"local transcript"}')
        elif self.path == "/api/generate":
            self.wfile.write(b'{"response":"Polished local transcript"}')
        else:
            self.wfile.write(b"{}")


class LocalClientIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.endpoint = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self) -> None:
        Handler.requests.clear()

    def test_memory_backed_asr_uses_loopback_and_returns_text(self) -> None:
        client = WhisperServer(self.endpoint)
        self.assertTrue(client.ready())
        self.assertEqual("local transcript", client.transcribe(b"\x00\x00"))
        path, headers, body = Handler.requests[-1]
        self.assertEqual("/inference", path)
        self.assertEqual("audio/wav", headers["Content-Type"])
        self.assertTrue(body.startswith(b"RIFF"))

    def test_whisper_runtime_is_supervised_for_service_lifetime(self) -> None:
        class Process:
            terminated = False
            def poll(self) -> None: return None
            def terminate(self) -> None: self.terminated = True
        process = Process()
        launched: list[object] = []
        def popen(*args: object, **kwargs: object) -> Process:
            launched.append(args[0])
            return process
        client = WhisperServer(self.endpoint, command=("whisper-server",), popen=popen)
        client.start()
        self.assertEqual([("whisper-server",)], launched)
        client.stop()
        self.assertTrue(process.terminated)

    def test_ollama_cleanup_uses_blessed_deterministic_request(self) -> None:
        client = OllamaClient(self.endpoint, "qwen3:4b-instruct-2507-q4_K_M")
        self.assertEqual("Polished local transcript", client.clean("local transcript", "Natural"))
        path, _, body = Handler.requests[-1]
        request = json.loads(body)
        self.assertEqual("/api/generate", path)
        self.assertFalse(request["stream"])
        self.assertFalse(request["think"])
        self.assertEqual(0, request["options"]["temperature"])
        self.assertEqual(2048, request["options"]["num_ctx"])
        self.assertEqual("5m", request["keep_alive"])


if __name__ == "__main__":
    unittest.main()


