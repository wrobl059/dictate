# Research: Local Dictation Runtime Decisions

## Long-lived whisper.cpp service

**Decision**: Supervise one localhost-only `whisper-server` from `dictate serve`, keeping the selected
model resident.

**Rationale**: The upstream server documentation describes a simple HTTP server, defaults to
`127.0.0.1`, and accepts inference requests. A resident process removes per-dictation model load cost
without embedding an ML framework. The application must verify loopback binding before use.

**Alternatives considered**: Spawn `whisper-cli` per session (simpler but reload latency); embed a Python
ML runtime (rejected: violates dependency/complexity budget).

## Audio representation

**Decision**: Capture mono 16 kHz signed 16-bit PCM with `sounddevice`; retain buffers in memory and
produce the smallest request representation whisper.cpp accepts.

**Rationale**: This is a conventional ASR-compatible format and avoids NumPy/conversion libraries.
Device-native mismatch is converted in Python memory. A temporary file is a last resort only when a
verified server interface cannot consume an in-memory request; it must be securely deleted and tested.

**Phase 3 status**: The implemented ASR client constructs the 16 kHz mono WAV request in `io.BytesIO`
and submits it directly to the loopback server. There is no normal temporary-audio path. T017 therefore
does not add a file fallback; it remains conditional on evidence that the memory-backed protocol is
unavailable.

## Ollama cleanup

**Decision**: Use `urllib.request` only against loopback Ollama, model
`qwen3:4b-instruct-2507-q4_K_M`, deterministic options, `think: false`, bounded context, and positive
keep-alive.

**Rationale**: Ollama documents a localhost API and generate endpoint. The standard library is sufficient
and keeps the model warm on a 16 GB baseline. Validate URL scheme, host resolution, and port before
sending content; reject any non-loopback configuration.

## Cleanup contract

**Decision**: One bounded prompt contains transcript, selected style, merged terms, and bounded target
context. Require output text only; instruct it to transform—not answer—and to preserve meaning.

**Rationale**: This separates “what was said” from “how it is written,” enabling a deterministic corpus
regression test. Reject empty or protocol-invalid output; never insert speculative fallback output.

## Platform boundaries

**Decision**: Use `pynput` as the first generic hotkey and injection mechanism. Implement narrow OS
adapters for permission diagnostics and target/context verification. Add native integration only where
the generic route demonstrably cannot meet a required platform behavior.

**Rationale**: It preserves a shared pipeline and avoids speculative per-platform dependencies. Fn is a
macOS preferred binding only if the installed adapter can observe it robustly; triggers are configurable.

## Configuration and dictionary

**Decision**: TOML preferences plus newline-delimited text dictionaries. Merge global first and let the
applicable project entry override a spelling for the session.

**Rationale**: Directly editable, inspectable, deterministic, and database-free.

## Explicit dependency acquisition

**Decision**: Make `dictate setup --install-dependencies` the sole mutable and network-permitted
bootstrap path. It performs an ordered discovery/acquisition/verification pass for the running
interpreter's declared Python dependencies, the supported whisper.cpp runtime, the default multilingual
`ggml-base.bin` speech model, the supported Ollama runtime, and the configured default Ollama model.
Bare `dictate setup` and `dictate doctor` only probe and explain how to invoke this path.

**Rationale**: It fulfills the one-command fresh-install requirement without making network access or
software changes part of ordinary setup, diagnostics, service startup, or dictation. Ordered outcomes
allow retries to retain a usable component and distinguish incomplete acquisition from final readiness.

**Alternatives considered**: Continue requiring manual installation (rejected: users must assemble the
default pipeline); acquire automatically from `serve` or ordinary setup (rejected: violates explicit
user initiation and offline expectations); embed ASR/cleanup runtimes as Python dependencies (rejected:
materially increases package size and complexity).

**Bootstrap detail**: Change the console entry point to a standard-library-only `bootstrap.py` module.
It recognizes only the explicit install invocation, uses the current Python interpreter to repair missing
declared package dependencies, then imports the ordinary CLI. This avoids importing audio or keyboard
modules before they can be installed and keeps all other commands on the existing normal CLI path.

## Installer boundary and verification

**Decision**: Add one small installer coordinator with injected process and download runners plus a
content-free per-component outcome type. Reuse readiness probes only after acquisition; extend preferences
with verified whisper executable and model locations so `serve` constructs the same loopback
`whisper-server` command that setup validated. Use atomic temporary downloads and verified replacement so
interrupted artifacts are never treated as installed.

**Rationale**: The existing flattened readiness result cannot identify which external artifact is missing,
and the current service has no production whisper-server command. A dedicated, testable coordinator closes
both gaps without a generalized provider architecture or content-bearing logs.

**Alternatives considered**: Infer install state from free-form readiness messages (rejected: ambiguous
and brittle); add a package-manager plugin system (rejected: unnecessary abstraction); leave service
startup externally managed after setup (rejected: setup could not verify the pipeline it installed).

## Cross-platform acquisition

**Decision**: Dispatch external-runtime installation through the existing platform adapter boundary. Each
supported platform uses one documented non-interactive acquisition route and reports a specific
content-free remedy when that route, authorization, storage, or platform support is unavailable. The
shared coordinator downloads the documented default speech model into Dictate-managed local application
data and verifies it before saving preferences.

**Rationale**: Runtime installation and authorization differ by operating system, while model lifecycle is
shared. This preserves a narrow, observable OS boundary and avoids silently choosing an unknown package
manager or escalating privileges.

**Alternatives considered**: A single shell script for every operating system (rejected: unsafe and
non-portable); silently attempt every installed package manager (rejected: surprising side effects);
require an elevated terminal (rejected: fails the actionable-remediation requirement).

