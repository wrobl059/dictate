# Quickstart Validation Guide

This guide validates the planned product; it does not prescribe implementation code.

## Prerequisites

- Python 3.11+ and a Dictate installation.
- Internet access only for this explicitly initiated initial acquisition.
- Sufficient local storage and any platform authorization required to acquire local runtimes.
- Platform permissions for microphone, global trigger/injection, text placement, and bounded context.

## First-run readiness

```bash
dictate setup --install-dependencies
dictate devices
dictate doctor
dictate serve
```

The explicit install command must acquire or retain declared Python package dependencies, whisper.cpp and
the default speech model, and Ollama with `qwen3:4b-instruct-2507-q4_K_M`; it must then verify them before
final readiness. A later bare `dictate setup` must perform no downloads or software changes. `doctor` must
identify a denied permission, unavailable microphone, missing executable/model, or non-loopback endpoint
without printing user content. See [CLI contract](contracts/cli.md).

## Acceptance checks

1. Start from a machine missing one or more default runtime/model components. Run `dictate setup
   --install-dependencies`; verify each component is reported as acquired or retained. Repeat the command
   and verify retained components are not reinstalled. Simulate an interrupted download, denied
   authorization, unavailable network, and unavailable storage; each result must identify the component,
   offer content-free remediation, and exit nonzero without reporting ready.
2. Disconnect Internet after successful setup. With `serve` running, dictate 20 scripted short samples; at least 19
   place text without manual copy/paste and at least 18 finish in five seconds.
3. Run the fixed cleanup corpus: filler/false starts, terminology, dictated questions, lists, and all four
   styles. Outputs must be transformation-only and preserve meaning.
4. Include unique sentinel content in audio-derived transcript, context, and cleanup output; inspect logs
   and application storage. No sentinel may be present.
5. Start in target A, move focus to target B before completion, and verify B receives no text. Verify any
   recovery result is in-process only and requires explicit action.
6. Deny context permission and verify setup reports a limitation with platform remediation without
   broadening collection or blocking context-free dictation.

Run unit tests for configuration parsing, dictionary merge, prompt construction, endpoint validation, and
state transitions; run localhost/process integration tests where runtimes are installed.

