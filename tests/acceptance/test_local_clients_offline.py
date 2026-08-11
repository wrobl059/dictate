from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path


class LocalClientOfflineAcceptanceTests(unittest.TestCase):
    def test_loopback_asr_and_cleanup_clients_complete_with_external_sockets_blocked(self) -> None:
        script = textwrap.dedent(
            """
            import json
            import socket
            import tempfile
            import threading
            from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
            from pathlib import Path

            from dictate.asr import WhisperServer
            from dictate.cleanup import OllamaClient
            from dictate.config import Preferences
            from dictate.offline import install_loopback_only_guard
            from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
            from dictate.service import DictationService, RecoveryStore

            SENTINEL = "offline-private-sentinel"
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, format, *args): pass
                def do_GET(self):
                    self.send_response(200); self.end_headers()
                def do_POST(self):
                    body = self.rfile.read(int(self.headers["Content-Length"]))
                    if self.path == "/inference":
                        if not self.headers["Content-Type"].startswith("multipart/form-data; boundary="): raise SystemExit("ASR did not receive multipart form data")
                        if b'name="file"; filename="audio.wav"' not in body or b"RIFF" not in body: raise SystemExit("ASR did not receive in-memory WAV file")
                        payload = {"text": SENTINEL}
                    elif self.path == "/api/generate":
                        request = json.loads(body)
                        if SENTINEL not in request["prompt"]: raise SystemExit("cleanup did not receive local transcript")
                        payload = {"response": "polished"}
                    else:
                        self.send_error(404); return
                    self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                    self.wfile.write(json.dumps(payload).encode())

            class Platform(PlatformAdapter):
                target = TargetSnapshot("app", "window", "field")
                def microphone_permission(self): return Capability(True)
                def trigger_permission(self): return Capability(True)
                def placement_permission(self): return Capability(True)
                def context_permission(self): return Capability(False)
                def snapshot_target(self): return self.target
                def read_context(self, target, limit): return None
                def target_matches(self, target): return target == self.target
                def insert_text(self, target, text): self.inserted = text; return True
                def start_hotkey(self, *args): pass
                def stop_hotkey(self): pass
                def recovery_instruction(self): return "recover"

            class Recorder:
                def start(self): pass
                def stop(self): return b"\\x00\\x00"
                def discard(self): pass

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            endpoint = f"http://127.0.0.1:{server.server_port}"
            install_loopback_only_guard()
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=0.1)
            except OSError:
                pass
            else:
                raise SystemExit("external socket was not blocked")
            with tempfile.TemporaryDirectory() as directory:
                platform = Platform()
                service = DictationService(
                    Preferences(asr_endpoint=endpoint, ollama_endpoint=endpoint), platform, Recorder(),
                    WhisperServer(endpoint), OllamaClient(endpoint, "qwen3:4b-instruct-2507-q4_K_M"), recovery=RecoveryStore(),
                )
                service.press(); service.release()
                if platform.inserted != "polished ": raise SystemExit("local clients did not complete pipeline")
                if list(Path(directory).iterdir()): raise SystemExit("pipeline persisted an artifact")
            server.shutdown(); server.server_close()
            print("local-clients-offline-pass")
            """
        )
        source_root = str(Path(__file__).parents[2] / "src")
        environment = os.environ | {"PYTHONPATH": source_root}
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=environment, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("local-clients-offline-pass\n", result.stdout)


if __name__ == "__main__":
    unittest.main()

