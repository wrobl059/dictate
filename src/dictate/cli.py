"""Command-line entry point; commands remain content-free by contract."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dictate.asr import WhisperServer
from dictate.audio import Recorder, list_input_devices
from dictate.cleanup import OllamaClient
from dictate.config import Preferences, load_preferences
from dictate.dictionary import global_dictionary_path, terms_for_paths
from dictate.installer import InstallerCoordinator
from dictate.platform import current_platform
from dictate.readiness import LocalReadiness
from dictate.service import DictationService, check_readiness
from dictate.startup import CombinedStartup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dictate", description="Local-only push-to-talk dictation")
    commands = parser.add_subparsers(dest="command")
    for name, help_text in (
        ("setup", "check required local setup"),
        ("serve", "start the local dictation service"),
        ("doctor", "run content-free readiness diagnostics"),
        ("devices", "list audio input devices"),
    ):
        command = commands.add_parser(name, help=help_text)
        if name == "setup":
            command.add_argument("--install-dependencies", action="store_true", help="explicitly acquire missing local default dependencies")
        if name == "serve":
            command.add_argument("--recover", action="store_true", help="print and clear an injected in-process recovery result (test-only)")
    return parser


def preferences_path(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".config" / "dictate" / "preferences.toml"


def _report_readiness(command: str, preferences: Preferences) -> int:
    try:
        platform = current_platform()
        result = check_readiness(preferences, LocalReadiness(platform))
    except Exception:
        print(f"{command}: configuration or local capability check failed", file=sys.stderr)
        return 1
    for limitation in result.limitations:
        print(f"{command}: limitation: {limitation}", file=sys.stderr)
    if not result.ready:
        for failure in result.required_failures:
            print(f"{command}: not ready: {failure}", file=sys.stderr)
        if command == "setup" and any(failure.startswith(("local ASR:", "local Ollama model:")) for failure in result.required_failures):
            print("setup: run dictate setup --install-dependencies to acquire missing default local components", file=sys.stderr)
        return 1
    print(f"{command}: ready")
    return 0


def _install_dependencies(preferences: Preferences, path: Path) -> tuple[bool, Preferences]:
    """Run the only mutable setup path and keep all output content-free."""
    coordinator = InstallerCoordinator(current_platform(), path)
    results = coordinator.install(preferences)
    failed = False
    for result in results:
        message = f"setup: {result.component}: {result.status}"
        if result.remediation:
            message = f"{message}: {result.remediation}"
        print(message, file=sys.stderr)
        failed = failed or result.status in ("failed", "unsupported")
    if failed:
        return False, preferences
    try:
        return True, load_preferences(path)
    except (OSError, ValueError):
        print("setup: verified local runtime settings could not be loaded", file=sys.stderr)
        return False, preferences


def _serve(preferences: Preferences) -> int:
    return CombinedStartup(preferences, current_platform()).run()


def main(argv: list[str] | None = None, *, recovery: object | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve" and args.recover:
        from dictate.service import DEFAULT_RECOVERY

        result = (recovery or DEFAULT_RECOVERY).take()
        if result is None:
            print("no recovery result is available", file=sys.stderr)
            return 1
        print(result)
        return 0
    path = preferences_path()
    try:
        preferences = load_preferences(path)
    except (OSError, ValueError):
        print(f"{args.command or 'dictate'}: invalid local preferences", file=sys.stderr)
        return 1
    if args.command == "devices":
        try:
            devices = list_input_devices()
        except Exception:
            print("devices: could not inspect local audio inputs", file=sys.stderr)
            return 1
        if not devices:
            print("devices: no local audio inputs are available", file=sys.stderr)
            return 1
        for device in devices:
            print(f"{device.identifier}\t{device.name}")
        return 0
    if args.command == "setup" and args.install_dependencies:
        installed, preferences = _install_dependencies(preferences, path)
        return _report_readiness("setup", preferences) if installed else 1
    if args.command in ("setup", "doctor"):
        return _report_readiness(args.command, preferences)
    return _serve(preferences)

