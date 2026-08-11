"""Command-line entry point; commands remain content-free by contract."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dictate", description="Local-only push-to-talk dictation")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("setup", "check required local setup"),
        ("serve", "start the local dictation service"),
        ("doctor", "run content-free readiness diagnostics"),
        ("devices", "list audio input devices"),
    ):
        command = commands.add_parser(name, help=help_text)
        if name == "serve":
            command.add_argument("--recover", action="store_true", help="print and clear this process's pending recovery result")
    return parser


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
    print(f"{args.command}: not available until its implementation phase", file=sys.stderr)
    return 0

