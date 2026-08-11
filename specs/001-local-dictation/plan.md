# Implementation Plan: Local Push-to-Talk Dictation

**Branch**: `001-local-dictation` | **Date**: 2026-08-11 | **Spec**: [spec.md](spec.md)

## Summary

Implement one Python 3.11+ command-line service: press → capture original target/context → record in
memory → release → local whisper.cpp ASR → local Ollama cleanup → re-verify original target → inject
text or retain an explicit local recovery result. The standard pipeline is offline-capable and contains
no cloud fallback, content history, telemetry, GUI, database, or web UI.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `sounddevice` 0.5.5 for cross-platform PortAudio capture; `pynput` 1.8.2 for
global key events and generic keyboard injection. `argparse`, `tomllib`, `logging`, `subprocess`,
`urllib.request`, `wave`, and `tempfile` alternatives are standard library. No NumPy, ML framework,
Ollama SDK, or other runtime dependency.

**External local runtimes**: whisper.cpp executable/service; Ollama with
`qwen3:4b-instruct-2507-q4_K_M`.

**Storage**: Directly editable TOML configuration and plain-text dictionaries only. Atomic writes for
preferences; no database. Audio, transcript, prompt, context, and successful output remain in memory.
An unsafe-placement recovery result is memory-only and cleared after explicit use, replacement, timeout,
or service exit.

**Testing**: `unittest` and standard-library fixtures; deterministic fakes at process/OS boundaries;
small fixed cleanup corpus; practical subprocess/localhost integration tests.

**Target Platform**: macOS, Windows, Linux. Python core is platform-neutral; platform adapters isolate
hotkey, target/context, permissions, and insertion behavior.

**Project Type**: Single CLI service.

**Performance Goals**: 90% of short ready-machine dictations visible within 5 seconds of release;
95% of 20 offline acceptance dictations complete without manual copy/paste.

**Constraints**: All normal content stays local; localhost inference endpoints must resolve to loopback;
no remote fallback; 16 GB baseline RAM; one active session; bounded context; no screenshots/OCR.

## Constitution Check

| Gate | Status | Plan evidence |
|---|---|---|
| Offline and local-only | PASS | Loopback-only verification; external binaries local; offline acceptance test |
| Privacy by architecture | PASS | In-memory content; metadata-only logs; no history/telemetry/clipboard default |
| Lowest complexity and CLI-first | PASS | One process, argparse, two Python dependencies, no GUI/database/framework |
| Cross-platform isolation | PASS | Narrow `platform/` adapters; shared pipeline |
| Faithful transformation | PASS | Strict cleanup contract and corpus prevents answers/invention |
| Observable tests | PASS | Offline, privacy, focus-safety, corpus, and integration tests |

**Post-design re-check**: PASS. `sounddevice` and `pynput` each satisfy a specific required OS boundary;
all other functionality uses Python or external local executables.

## Architecture and Delivery Sequence

1. Create package/CLI/config/dictionary/logging foundations and deterministic state machine.
2. Add audio capture and session lifecycle using 16 kHz mono signed-16-bit PCM; adapt capture format in
   memory only when needed for whisper.cpp, with no conversion dependency.
3. Add a long-lived localhost `whisper-server` process, launched and supervised by the service so its
   model remains resident. Send in-memory audio as a request body; pass bounded dictionary terms as the
   supported initial-prompt/bias input. If server protocol cannot accept memory audio reliably on all
   targets, use a securely created temporary file deleted in a `finally` block and add a privacy test;
do not persist normal audio.
4. Add standard-library `urllib.request` Ollama client. It accepts only `http://127.0.0.1` or
   `http://localhost` resolving solely to loopback; use non-streaming generate/chat, `think: false`,
   temperature 0, bounded `num_ctx`, and a positive `keep_alive`. Verify configured model and warm it
   during readiness checks.
5. Add isolated platform adapters. Generic `pynput` is the first hotkey/insertion path; macOS Fn support
   is optional only if accessible through that adapter. Use native platform behavior only after a
   documented generic failure. Target identity is captured at key-down and must match at insertion.
6. Implement setup/doctor/devices/serve, then corpus and end-to-end acceptance tests.

## Project Structure

```text
src/dictate/
├── __main__.py          # argparse entry point
├── cli.py               # setup, serve, doctor, devices
├── config.py            # TOML files and defaults
├── service.py           # orchestration and readiness
├── session.py           # explicit dictation state machine
├── audio.py             # sounddevice in-memory PCM capture
├── asr.py               # whisper.cpp supervisor/client
├── cleanup.py           # loopback-only Ollama client and prompt construction
├── dictionary.py        # text dictionary loading and precedence
├── context.py           # bounded context model
├── privacy.py           # redacted operational logging and local endpoint checks
└── platform/            # base contract plus macos/windows/linux adapters

tests/
├── unit/
├── integration/
├── acceptance/
└── fixtures/cleanup-corpus.json
```

**Structure Decision**: One ordinary Python package; no provider/plugin abstraction. The platform folder
is the only polymorphic boundary because OS behavior is intrinsically different.

## Complexity Tracking

No constitutional violations or additional architectural layers require justification.
