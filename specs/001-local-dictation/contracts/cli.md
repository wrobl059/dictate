# CLI Contract

## Commands

| Command | Contract |
|---|---|
| `dictate setup` | Performs no installation or download. Verifies local runtimes/models, selected/default microphone, trigger monitoring, and safe text placement. Reports ready only when required capabilities pass; unavailable destination context is a non-blocking limitation with platform remediation. When a default runtime or model is missing, reports the component and recommends `dictate setup --install-dependencies`. |
| `dictate setup --install-dependencies` | The sole user-initiated dependency acquisition command. Repairs missing declared Python package dependencies for the current interpreter, then retains or acquires and verifies the supported whisper.cpp runtime, default speech model, Ollama runtime, and configured default Ollama model. Performs final normal readiness checks after acquisition. Network use is permitted only for this explicit command. |
| `dictate` | Starts the single long-running service and its unavailable installed local inference dependencies. It reuses compatible pre-existing local dependencies, starts only dependencies it owns, and emits metadata-only status to stderr. |
| `dictate serve` | Compatibility alias for `dictate`. |
| `dictate doctor` | Executes real capability checks and prints actionable, platform-specific remediation without content. Exit nonzero when a required capability fails. |
| `dictate devices` | Lists audio input identifiers and display names without recording content. |

## Exit and output rules

- Commands use stdout for requested data and stderr for status/errors.
- Ordinary logs/output MUST NOT contain audio, transcript, context, prompt, or generated text.
- `serve` does not expose an HTTP interface.
- A combined invocation stops only dependency processes it launched; it leaves pre-existing compatible dependencies running.
- A second combined invocation fails safely without attaching to, stopping, or reconfiguring the active invocation.
- A non-loopback ASR/Ollama endpoint is a hard configuration error, never a fallback decision.
- `setup --install-dependencies` prints only component identity, terminal status, and content-free
  remediation. It exits nonzero when any component acquisition/verification or final required readiness
  check fails; it does not claim ready after partial success.
- Existing verified components are reported as retained and are not reinstalled. Interrupted or incomplete
  artifacts are not reported as retained and may be safely reacquired on a later explicit invocation.

## Service event contract

`press`: snapshot target/context, then begin capture. `release`: stop capture and run local ASR then cleanup.
Insert only after exact target revalidation. On focus mismatch retain an in-memory recovery result; on ASR or
cleanup failure discard content and report only a content-free actionable error.

