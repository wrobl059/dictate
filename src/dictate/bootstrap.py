"""Standard-library-only console dispatcher for explicit dependency repair."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys
from collections.abc import Callable, Sequence

PYTHON_DEPENDENCIES = ("sounddevice==0.5.5", "pynput==1.8.2")


def is_explicit_install(argv: Sequence[str]) -> bool:
    """Accept exactly the one command permitted to modify dependencies."""
    return tuple(argv) == ("setup", "--install-dependencies")


def missing_dependencies() -> tuple[str, ...]:
    missing: list[str] = []
    for requirement in PYTHON_DEPENDENCIES:
        name, _, expected = requirement.partition("==")
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed = None
        if installed != expected:
            missing.append(requirement)
    return tuple(missing)


def repair_dependencies(
    requirements: Sequence[str], runner: Callable[[Sequence[str]], int] | None = None
) -> bool:
    if not requirements:
        return True
    run = runner or (lambda command: subprocess.run(tuple(command), check=False).returncode)
    try:
        return run((sys.executable, "-m", "pip", "install", *requirements)) == 0
    except OSError:
        return False


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: Callable[[Sequence[str]], int] | None = None,
    import_cli: Callable[[], Callable[[list[str] | None], int]] | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if is_explicit_install(arguments) and not repair_dependencies(missing_dependencies(), runner):
        print("setup: Python dependencies could not be installed; verify network access and retry", file=sys.stderr)
        return 1
    if import_cli is None:
        from dictate.cli import main as cli_main

        import_cli = lambda: cli_main
    return import_cli()(arguments)

