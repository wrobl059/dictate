from __future__ import annotations

import unittest
from unittest.mock import patch

from dictate import bootstrap


class BootstrapTests(unittest.TestCase):
    def test_explicit_install_repairs_only_missing_declared_dependencies_before_cli(self) -> None:
        calls: list[tuple[str, ...]] = []
        with patch("dictate.bootstrap.missing_dependencies", return_value=("sounddevice==0.5.5",)):
            result = bootstrap.main(
                ["setup", "--install-dependencies"],
                runner=lambda command: calls.append(tuple(command)) or 0,
                import_cli=lambda: lambda arguments: 7 if arguments == ["setup", "--install-dependencies"] else 1,
            )
        self.assertEqual(7, result)
        self.assertEqual(1, len(calls))
        self.assertEqual(("-m", "pip", "install", "sounddevice==0.5.5"), calls[0][1:])

    def test_all_non_exact_install_commands_skip_dependency_repair(self) -> None:
        for arguments in ([], ["setup"], ["doctor"], ["devices"], ["serve"], ["setup", "--other"]):
            with self.subTest(arguments=arguments):
                with patch("dictate.bootstrap.repair_dependencies") as repair:
                    self.assertEqual(0, bootstrap.main(arguments, import_cli=lambda: lambda _arguments: 0))
                repair.assert_not_called()

    def test_failed_repair_does_not_import_cli(self) -> None:
        with patch("dictate.bootstrap.missing_dependencies", return_value=("pynput==1.8.2",)):
            self.assertEqual(
                1,
                bootstrap.main(["setup", "--install-dependencies"], runner=lambda _command: 1, import_cli=lambda: self.fail("CLI must not import")),
            )


if __name__ == "__main__":
    unittest.main()

