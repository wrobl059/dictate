# Quickstart Validation Guide

This guide validates the planned product; it does not prescribe implementation code.

## Prerequisites

- Python 3.11+ with the two approved runtime dependencies.
- Locally installed whisper.cpp and a local model.
- Locally installed Ollama with `qwen3:4b-instruct-2507-q4_K_M` available.
- Platform permissions for microphone, global trigger/injection, text placement, and bounded context.

## First-run readiness

```bash
dictate setup
dictate devices
dictate doctor
dictate serve
```

`setup` must report ready only after all required local capabilities pass. `doctor` must identify a denied
permission, unavailable microphone, missing executable/model, or non-loopback endpoint without printing
user content. See [CLI contract](contracts/cli.md).

## Acceptance checks

1. Disconnect Internet after setup. With `serve` running, dictate 20 scripted short samples; at least 19
   place text without manual copy/paste and at least 18 finish in five seconds.
2. Run the fixed cleanup corpus: filler/false starts, terminology, dictated questions, lists, and all four
   styles. Outputs must be transformation-only and preserve meaning.
3. Include unique sentinel content in audio-derived transcript, context, and cleanup output; inspect logs
   and application storage. No sentinel may be present.
4. Start in target A, move focus to target B before completion, and verify B receives no text. Verify any
   recovery result is in-process only and requires explicit action.
5. Deny context permission and verify setup fails with platform remediation without broadening collection.

Run unit tests for configuration parsing, dictionary merge, prompt construction, endpoint validation, and
state transitions; run localhost/process integration tests where runtimes are installed.

