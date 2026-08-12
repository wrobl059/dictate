# CLI Contract: Unified Dictate Startup

## Commands

```text
dictate
dictate serve
dictate setup
dictate setup --install-dependencies
dictate doctor
dictate devices
```

| Command | Contract |
| --- | --- |
| `dictate` | Starts the foreground combined Dictate invocation. It coordinates required local dependency services and enters normal dictation only after readiness succeeds. |
| `dictate serve` | Compatibility alias with the same combined-invocation behavior and exit semantics as `dictate`. |
| `dictate setup` | Read-only readiness/configuration probe; never acquires or launches dependencies. |
| `dictate setup --install-dependencies` | The sole explicit path allowed to acquire/install local runtimes, models, and package dependencies. |
| `dictate doctor` | Read-only, content-free diagnostic; never acquires or launches dependencies. |
| `dictate devices` | Lists available input devices; never launches dependencies. |

## Combined Invocation Lifecycle

1. Validate configured dependency endpoints as local-only before making any content-bearing request or launching a dependency.
2. Acquire the single-invocation runtime lock. On contention, exit safely without managing dependency processes.
3. Probe the speech-recognition and cleanup dependencies. Mark each responding compatible local service as pre-existing.
4. Start only dependencies that are unavailable and record them as owned by this invocation.
5. Poll the complete readiness contract for no more than 30 seconds.
6. Start Dictate only after all required readiness checks succeed, then print the ready status and run until interrupted or a required owned dependency is lost.
7. On interruption, failed startup, timeout, or runtime dependency loss, stop Dictate and then stop only invocation-owned dependencies in reverse launch order. Release the runtime lock.

## Output and Exit Behavior

- Readiness is emitted exactly once per successful combined invocation, after Dictate and all required local capabilities are ready.
- Startup, status, failure, and shutdown output uses fixed component/state/remediation language only. It MUST NOT contain audio, transcripts, context, prompts, generated text, or user-provided dictionary entries.
- A missing runtime, model, executable, or verified artifact is a non-ready failure that directs the user to `dictate setup --install-dependencies`; it never triggers automatic acquisition.
- Unsafe remote or non-loopback dependency endpoints are hard failures. The command MUST not launch, use, or fall back to a remote service.
- Permission, device, hotkey, placement, launch, model, and timeout failures are non-ready failures. The command MUST not accept dictation after any such failure.
- Lock contention fails with a fixed “Dictate is already running” message and no launch, attachment, reconfiguration, or shutdown of the other invocation.
- Normal terminal interruption exits cleanly after owned-process cleanup. A failure exits non-zero; a normal user interruption may use the conventional interruption exit status.

## Ownership Rules

| Dependency state at invocation start | Startup action | Shutdown action |
| --- | --- | --- |
| Compatible local service is ready | Reuse it as pre-existing | Leave it running |
| Service is unavailable | Launch the installed local service and await readiness | Stop it if this invocation launched it |
| Endpoint is unsafe or incompatible | Fail before launch/use | Do not manage any external service |
| Another invocation holds the lock | Fail safely | Do not manage any service |

## Compatibility and Boundaries

- The normal dictation workflow after ready—push-to-talk capture, local transcription, local cleanup, focus/target revalidation, and text insertion—retains its existing contract.
- This contract adds no HTTP API, GUI, persistent daemon, remote access, cloud fallback, or user-content history.

