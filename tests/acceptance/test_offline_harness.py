from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path


class OfflineHarnessAcceptanceTests(unittest.TestCase):
    def test_service_process_blocks_external_socket_and_completes_pipeline(self) -> None:
        script = textwrap.dedent(
            """
            import socket
            from dictate.config import Preferences
            from dictate.offline import install_loopback_only_guard
            from dictate.platform.base import Capability, PlatformAdapter, TargetSnapshot
            from dictate.service import DictationService, RecoveryStore
            install_loopback_only_guard()
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=0.1)
            except OSError:
                pass
            else:
                raise SystemExit("external socket was not blocked")
            class P(PlatformAdapter):
                def microphone_permission(self): return Capability(True)
                def trigger_permission(self): return Capability(True)
                def placement_permission(self): return Capability(True)
                def context_permission(self): return Capability(False)
                def snapshot_target(self): return TargetSnapshot("a", "w", "t")
                def read_context(self, target, limit): return None
                def target_matches(self, target): return True
                def insert_text(self, target, text): self.inserted = True; return True
                def start_hotkey(self, *args): pass
                def stop_hotkey(self): pass
                def recovery_instruction(self): return "recover"
            class R:
                def start(self): pass
                def stop(self): return b"pcm"
                def discard(self): pass
            class A:
                def start(self): pass
                def stop(self): pass
                def transcribe(self, pcm, terms=()): return "spoken"
            class C:
                def clean(self, transcript, style, terms=(), context=None): return "polished"
            platform = P()
            service = DictationService(Preferences(), platform, R(), A(), C(), recovery=RecoveryStore())
            service.press(); service.release()
            if not getattr(platform, "inserted", False): raise SystemExit("pipeline did not insert")
            print("offline-guard-pass")
            """
        )
        source_root = str(Path(__file__).parents[2] / "src")
        environment = os.environ | {"PYTHONPATH": source_root}
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=environment, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("offline-guard-pass\n", result.stdout)


if __name__ == "__main__":
    unittest.main()

