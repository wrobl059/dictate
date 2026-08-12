# Research: Unified Dictate Startup

## Decision: Use an invocation-scoped supervisor

Create a small `startup.py` coordinator that is called by no-argument `dictate` and the retained `serve` alias. It owns the sequence: validate local configuration, probe dependencies, launch only unavailable dependencies, wait for readiness, start `DictationService`, and clean up in `finally`.

**Rationale**: Current CLI logic performs readiness before starting the application, while Whisper process supervision is optional and unused by the CLI and Ollama has only a content-bearing HTTP client. A coordinator centralizes ownership, timeout, interruption, and lock semantics without entangling argument parsing, installer acquisition, or platform target operations.

**Alternatives considered**:

- Put all lifecycle logic in `cli.py`: rejected because it makes parsing, output, process ownership, polling, and cleanup difficult to test independently.
- Extend `DictationService` to launch dependencies: rejected because the service should retain responsibility for hotkey/dictation lifecycle, not external process ownership.
- Add a resident daemon with an attachment protocol: rejected as unnecessary complexity for one active local CLI invocation.

## Decision: Keep process boundaries separate from inference clients

Keep `WhisperServer` and `OllamaClient` focused on local inference/readiness requests. Provide a narrow managed process boundary for each executable; build Whisper's command from existing verified preferences and introduce the equivalent injected command/process boundary for Ollama.

**Rationale**: Separating launch/stop from content-bearing requests makes it explicit that only the supervisor decides ownership. It enables deterministic process tests and prevents a client connected to a pre-existing service from terminating it.

**Alternatives considered**:

- Make every client always launch its own service: rejected because it cannot preserve pre-existing services and obscures ownership.
- Use platform installer adapters to launch processes: rejected because those interfaces are explicitly for acquisition and may perform network-enabled package operations.

## Decision: Probe first, then launch only unavailable local dependencies

Before launching each dependency, validate both configured endpoints with existing loopback URL validation and issue the existing content-free readiness probe. Mark a responding compatible service as pre-existing; otherwise attempt to start the corresponding local executable. Poll readiness until the shared deadline.

**Rationale**: This meets the one-command experience while retaining FR-010 ownership behavior. Existing URL validation rejects remote, authenticated, and non-HTTP endpoints before content-bearing processing can begin.

**Alternatives considered**:

- Always launch both executables: rejected because it produces port conflicts and risks disturbing manually managed services.
- Treat a listening port as ready: rejected because model/application readiness is required in addition to a TCP listener.

## Decision: Use bounded polling and fixed, content-free startup status

Use an injected monotonic clock and sleeper to poll existing readiness checks until a 30-second deadline. Report only fixed component names, readiness state, and explicit remediation. Do not include exception strings that could contain configuration or user content.

**Rationale**: Readiness currently proves ASR, model, microphone, trigger, and placement capabilities but has no startup wait. Deterministic polling supports testability and prevents premature ready status.

**Alternatives considered**:

- Fixed sleep after process launch: rejected because startup time varies and can falsely report readiness.
- Unbounded retries: rejected because it leaves users with a hung terminal and complicates cleanup.

## Decision: Fail safely on concurrent invocation via a transient local lock

Acquire a lock before launching or supervising dependencies. If another invocation owns it, print a fixed “already running” remediation and exit without launching or stopping any dependency. Remove the lock in `finally`, including failed startup and interruption paths.

**Rationale**: Safe failure satisfies the feature without needing an attachment/control protocol. It eliminates ownership ambiguity during another process's startup window.

**Alternatives considered**:

- Attach to the existing invocation: deferred; it needs a local control protocol and explicit process identity verification.
- Infer ownership from endpoint availability: rejected because endpoint state cannot safely identify which invocation owns a process.

## Decision: Preserve explicit setup as the sole acquisition boundary

The default command and `serve` alias must never call `InstallerCoordinator`, package repair, model acquisition, or external runtime acquisition. Missing executable, model, or verified artifact produces a fixed failure directing the user to `dictate setup --install-dependencies`.

**Rationale**: The existing bootstrap and installer already enforce this boundary, which is required for offline normal operation and privacy.

**Alternatives considered**:

- Install missing dependencies while starting: rejected because it violates the explicit-user-action, offline-normal-operation contract.

## Decision: Stop only owned processes in reverse order

On normal interruption, startup failure, readiness timeout, application startup failure, or owned dependency loss: stop DictationService first, then stop only managed dependencies started by the invocation in reverse launch order. Process stop must be idempotent and bounded, using graceful termination followed by escalation if necessary.

**Rationale**: Reverse order removes dependents before their providers and preserves pre-existing services. Idempotence supports repeated cleanup through error and signal paths.

**Alternatives considered**:

- Let child processes outlive the CLI: rejected because it violates lifecycle ownership and leaves accidental background work.
- Stop every reachable dependency: rejected because it may stop user-managed or another invocation's service.

