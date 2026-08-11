from __future__ import annotations

import contextlib
import io
import unittest

from dictate.cli import main
from dictate.service import RecoveryStore


class RecoveryAcceptanceTests(unittest.TestCase):
    def test_recovery_is_stdout_only_once_and_memory_only(self) -> None:
        store = RecoveryStore()
        store.put("final result")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(0, main(["serve", "--recover"], recovery=store))
            self.assertEqual(1, main(["serve", "--recover"], recovery=store))
        self.assertEqual("final result\n", stdout.getvalue())
        self.assertNotIn("final result", stderr.getvalue())

    def test_timeout_and_replacement_clear_old_result(self) -> None:
        now = [0.0]
        store = RecoveryStore(timeout_seconds=1, clock=lambda: now[0])
        store.put("old")
        store.put("new")
        self.assertEqual("new", store.take())
        store.put("expired")
        now[0] = 2.0
        self.assertIsNone(store.take())


if __name__ == "__main__":
    unittest.main()

