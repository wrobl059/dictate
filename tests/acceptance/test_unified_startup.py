from __future__ import annotations

import contextlib
import io
import unittest
from typing import cast
from unittest.mock import patch

from dictate.config import Preferences
from dictate.platform.base import PlatformAdapter
from dictate.startup import CombinedStartup


class UnifiedStartupAcceptanceTests(unittest.TestCase):
    def test_bare_cli_uses_combined_startup_without_installer_acquisition(self) -> None:
        from dictate.cli import main

        output, errors = io.StringIO(), io.StringIO()
        with patch("dictate.cli.load_preferences", return_value=Preferences()), patch("dictate.cli.current_platform", return_value=object()), patch("dictate.cli.CombinedStartup") as startup_type, patch("dictate.cli.InstallerCoordinator") as installer, contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            startup_type.return_value.run.return_value = 0
            self.assertEqual(0, main([]))
        installer.assert_not_called()
        startup_type.assert_called_once()
        self.assertEqual("", output.getvalue())
        self.assertEqual("", errors.getvalue())

    def test_unsafe_endpoint_output_excludes_content_sentinel(self) -> None:
        sentinel = "private dictated transcript"
        messages: list[str] = []
        startup = CombinedStartup(Preferences(asr_endpoint="http://example.com:8080"), cast(PlatformAdapter, object()), status=messages.append)
        self.assertEqual(1, startup.run())
        self.assertTrue(messages)
        self.assertNotIn(sentinel, "\n".join(messages))


if __name__ == "__main__":
    unittest.main()


