# CLI Contract

## Commands

| Command | Contract |
|---|---|
| `dictate setup` | Verifies/assists explicit installation of local runtimes and models, selected/default microphone, trigger monitoring, text placement, and required context access. Reports ready only when all pass. Network use is permitted only for user-initiated installation/model acquisition. |
| `dictate serve` | Starts the single long-running service. Defaults to OS microphone, platform-appropriate trigger, Natural style, local whisper.cpp, loopback Ollama, and no content history. Emits metadata-only status to stderr. |
| `dictate doctor` | Executes real capability checks and prints actionable, platform-specific remediation without content. Exit nonzero when a required capability fails. |
| `dictate devices` | Lists audio input identifiers and display names without recording content. |

## Exit and output rules

- Commands use stdout for requested data and stderr for status/errors.
- Ordinary logs/output MUST NOT contain audio, transcript, context, prompt, or generated text.
- `serve` does not expose an HTTP interface.
- A non-loopback ASR/Ollama endpoint is a hard configuration error, never a fallback decision.

## Service event contract

`press`: snapshot target/context, then begin capture. `release`: stop capture and run local ASR then cleanup.
Insert only after exact target revalidation. On focus mismatch retain an in-memory recovery result; on ASR or
cleanup failure discard content and report only a content-free actionable error.

