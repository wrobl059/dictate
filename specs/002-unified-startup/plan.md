# Implementation Plan: Unified Dictate Startup

**Branch**: `002-unified-startup` | **Date**: 2026-08-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-unified-startup/spec.md`

## Summary

Make the installed `dictate` command the standard long-running entry point: safely coordinate locally installed Whisper and Ollama processes, wait for the complete Dictate readiness contract, and run the current dictation service. Add an invocation-scoped supervisor that probes dependencies before starting them, records ownership, polls existing content-free readiness checks under a bounded deadline, and stops only processes it launched. Keep `serve` as a compatibility alias and leave dependency acquisition exclusively in `setup --install-dependencies`.

## Technical Context

**Language/Version**: Python 3.11 or later

**Primary Dependencies**: Standard-library process, signal, URL, and time facilities; existing `sounddevice`, `pynput`, and platform-specific PyObjC packages; locally installed Whisper and Ollama executables

**Storage**: Existing local preferences and installer verification artifacts only; invocation ownership is in memory plus a transient local runtime lock with no user content

**Testing**: Python `unittest` discovery; existing unit, integration, and acceptance suites using fake loopback services and injected process handles

**Target Platform**: macOS, Windows, and Linux; platform readiness/placement support remains authoritative

**Project Type**: Local-first command-line application and long-running service

**Performance Goals**: In at least 95% of successful installed-system starts, report ready within 30 seconds; do not start DictationService until every required capability is ready

**Constraints**: Offline normal operation; loopback-only dependency endpoints; no automatic acquisition, cloud fallback, telemetry, persistence, or content in status output; cleanup must be bounded and idempotent; retain `serve` compatibility

**Scale/Scope**: One interactive local user and one active invocation per user runtime directory; no multi-user service, attachment/control protocol, GUI, or persistent daemon

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Pre-design gate: PASS**

- **Local-only operation**: The supervisor launches and verifies only local dependency endpoints. It does not invoke the installer or any network acquisition path, and all normal-path readiness and inference remain offline.
- **Privacy by architecture**: Status, lock metadata, and logs contain fixed component/status information only. Audio, transcripts, prompts, context, and generated text remain in memory and are never used for supervision diagnostics.
- **Lowest reasonable complexity**: A small supervisor and one Ollama process boundary reuse existing clients, `LocalReadiness`, `DictationService`, and standard-library process primitives. No new framework, database, daemon protocol, or platform process layer is introduced.
- **CLI first and opinionated defaults**: No-argument `dictate` becomes the single default startup command; `serve` remains an alias. The existing explicit setup, diagnostic, and configuration commands remain separate.
- **Cross-platform boundaries**: Process orchestration is platform-neutral; existing adapters continue to own permissions, hotkey, placement, and acquisition behavior.
- **Fast/safe behavior and faithful transformation**: The existing dictation pipeline is unchanged and cannot run until safe readiness succeeds.
- **Observable verification**: The implementation will add deterministic ownership, cleanup, lock-contention, offline, and content-free-output coverage.

**Post-design gate: PASS** — The proposed data model, CLI contract, and quickstart preserve all pre-design guarantees. The runtime lock is transient operational metadata, has no user content, and is removed on all exits; a locked invocation fails safely rather than attaching to or controlling another process.

## Project Structure

### Documentation (this feature)

```text
specs/002-unified-startup/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md               # Created by /speckit-tasks, not this phase
```

### Source Code (repository root)

```text
src/dictate/
├── bootstrap.py           # Explicit-install-only bootstrap remains unchanged
├── cli.py                 # No-argument dispatch and compatibility alias
├── startup.py             # New invocation-scoped dependency supervisor
├── asr.py                 # Whisper process boundary and client
├── cleanup.py             # Ollama process boundary and client
├── readiness.py           # Existing content-free capability probes
├── service.py             # Existing DictationService lifecycle
└── platform/              # Existing OS-only permissions/target/placement boundaries

tests/
├── unit/
│   ├── test_cli.py
│   ├── test_startup.py    # New supervisor, ownership, timeout, and lock tests
│   └── test_local_clients.py
├── integration/
│   └── test_unified_startup.py
└── acceptance/
    └── test_unified_startup.py
```

**Structure Decision**: Keep the existing single Python package and test layout. Add `startup.py` as the narrow composition root for lifecycle ownership rather than mixing dependency process control into CLI parsing, installer acquisition, platform adapters, or content-bearing inference clients.
