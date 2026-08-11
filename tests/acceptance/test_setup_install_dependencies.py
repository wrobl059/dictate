from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class SetupInstallDependenciesAcceptanceTests(unittest.TestCase):
    def test_explicit_install_reports_ordered_results_without_sensitive_fixture_data(self) -> None:
        script = textwrap.dedent(
            """
            import contextlib
            import io
            from unittest.mock import patch
            from dictate.config import Preferences
            from dictate.installer import ComponentResult
            from dictate.service import ReadinessResult
            from dictate.cli import main

            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output), \\
                 patch('dictate.cli.current_platform', return_value=object()), \\
                 patch('dictate.cli.load_preferences', return_value=Preferences()), \\
                 patch('dictate.cli.check_readiness', return_value=ReadinessResult((), ())), \\
                 patch('dictate.cli.InstallerCoordinator') as coordinator:
                coordinator.return_value.install.return_value = (
                    ComponentResult('python-dependencies', 'retained'),
                    ComponentResult('whisper-runtime', 'acquired'),
                    ComponentResult('whisper-model', 'acquired'),
                    ComponentResult('ollama-runtime', 'retained'),
                    ComponentResult('ollama-model', 'retained'),
                )
                assert main(['setup', '--install-dependencies']) == 0
            value = output.getvalue()
            assert value.index('python-dependencies') < value.index('whisper-runtime') < value.index('whisper-model')
            assert 'unique-sensitive-fixture' not in value
            """
        )
        environment = os.environ | {"PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()

