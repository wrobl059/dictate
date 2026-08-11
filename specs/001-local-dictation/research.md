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

