# Dictate

A local-only push-to-talk dictation service. Its supported pipeline is:

```
press → in-memory microphone capture → local whisper.cpp → local Ollama cleanup → target revalidation → insert or recovery
```

It has no cloud fallback, telemetry, web service, GUI, database, clipboard fallback, or default content history.

## Requirements

- Python 3.11 or newer
- A Dictate installation; `dictate setup --install-dependencies` repairs the declared Python package dependencies when needed
- Local storage, network access, and any platform authorization required for the one-time explicit acquisition
- A microphone and platform permissions for microphone access, global keyboard monitoring, and verified text placement

Local runtime and model installation is a user-initiated setup operation. Normal dictation must work with the Internet disconnected after those local components are ready.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
dictate setup --install-dependencies
```

This is the only command that installs or downloads dependencies. It acquires or retains the supported
whisper.cpp runtime, `ggml-base.bin` speech model, Ollama runtime, and
`qwen3:4b-instruct-2507-q4_K_M` cleanup model, then verifies local readiness. Repeat it safely: verified
components are retained. If a platform route, authorization, storage, network connection, download, or
verification fails, setup names only the affected component and remediation; it never reports ready after
partial acquisition. Do not configure either inference endpoint to a non-loopback address.

## Start Dictate

After explicit setup, start the complete local pipeline with one command:

```bash
dictate
```

Dictate verifies loopback-only endpoints, reuses a compatible already-running local service, or starts the
installed whisper.cpp and Ollama services itself. It reports ready only after both inference dependencies,
microphone, trigger, and safe text placement are available. `dictate serve` remains a compatibility alias.

Stop with `Ctrl-C`. Dictate stops only dependency processes that it started; pre-existing compatible services are
left running. A second combined invocation exits safely rather than controlling the active invocation. Missing
runtimes or models never trigger a download: run `dictate setup --install-dependencies` explicitly.

## Command contract

```bash
dictate setup
dictate setup --install-dependencies
dictate devices
dictate doctor
dictate serve
```

- `setup` only verifies the required local components. It never downloads or changes host software; missing
  default runtime/model components are remediated with `dictate setup --install-dependencies`.
- `setup --install-dependencies` is the explicit, content-free acquisition path. Normal dictation and all
  other commands remain offline-capable after it succeeds.
- `devices` lists local input identifiers and display names without recording.
- `doctor` prints content-free readiness failures and platform-specific remediation. On macOS, it requests
  Microphone access through the native authorization API without opening, sampling, or retaining audio.
- `dictate` starts the local inference dependencies and push-to-talk pipeline after required local readiness checks pass.
- `serve` is a compatibility alias for `dictate`.

The repository's acceptance tests exercise the service through deterministic local boundaries. On macOS, Dictate
captures and revalidates the original application, window, and editable text target before placement. Verified
browser address bars and Gmail-style editable recipient fields use native Accessibility replacement. Slack uses
direct Quartz Unicode key events after the same verification because its Accessibility setter may acknowledge a
write without displaying it. Terminal applications are currently unsupported and fail closed. A pending
unsafe-placement result remains in process memory only; an interactive recovery UX is not yet available.

## Blessed defaults

A fresh configuration uses one supported pipeline:

| Setting | Default |
|---|---|
| Microphone | `system-default` |
| Trigger | `right_alt` |
| Style | `Natural` |
| Local ASR endpoint | `http://127.0.0.1:8080` |
| Speech model | `ggml-base.bin` |
| Local Ollama endpoint | `http://127.0.0.1:11434` |
| Cleanup model | `qwen3:4b-instruct-2507-q4_K_M` |
| Context limit | 1,024 characters |

On macOS, `right_alt` means the physical **right Option/Alt** key (reported by pynput as `alt_r`). Hold it while speaking, then release it to stop recording and start local processing. Grant Input Monitoring to the app that launches Dictate so it can receive the global key events.

The built-in cleanup styles are Natural, Formal, Casual, and Technical. Cleanup is mandatory, deterministic local Ollama processing; it transforms what was dictated and must not answer questions or add content.

## Privacy and safety

Audio, transcript, bounded destination context, dictionary terms, prompts, generated text, and a recovery result stay in memory for the active session. They are cleared after placement, failure, recovery consumption, timeout, or service exit. Ordinary logs and diagnostics contain status, timing, sizes, and error metadata only.

Both ASR and Ollama endpoints are validated as loopback-only before content can be sent. A remote endpoint is a hard configuration error, not a fallback choice.

Destination context is optional. If the platform cannot provide its bounded target-local context, diagnostics report the limitation and dictation proceeds without context. Screen capture, OCR, and collection from unrelated applications are not used.

Text is injected only after revalidating the original application, window, and text target captured at key-down. If that check fails, no destination receives text; the result is retained only in process memory pending an explicit recovery interaction.

## Platform behavior and validation

The cross-platform acceptance contract and the current content-free evidence are in [`specs/001-local-dictation/platform-acceptance-matrix.md`](specs/001-local-dictation/platform-acceptance-matrix.md). The generic key-monitoring path is shared. macOS uses verified native Accessibility placement for standard editable controls and verified Quartz Unicode input for Slack; Terminal is intentionally unsupported. Windows and Linux remain fail-closed until their platform has a verified original-target implementation.

The warmed-model latency acceptance target is visible placement within five seconds of release for at least 90% of successful short dictations. The timing report carries only duration and outcome metadata.

## Validate

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The acceptance suite includes offline socket blocking, focus safety, privacy lifecycle checks, the common platform matrix, and a deterministic synthetic short-audio latency fixture.


