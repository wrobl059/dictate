# Data Model: Unified Dictate Startup

This feature introduces only transient operational state. It does not store audio, transcripts, context, prompts, generated text, or other user content.

## Combined Invocation

Represents one foreground `dictate` command execution.

| Field | Description | Validation |
| --- | --- | --- |
| invocation identifier | Opaque runtime identifier for lock ownership and diagnostics | Generated locally; never derived from user content |
| state | `starting`, `waiting_ready`, `ready`, `recovering`, `stopping`, or `stopped` | State advances only through defined transitions |
| deadline | Monotonic time by which readiness must succeed | Must be no more than 30 seconds after startup begins |
| lock ownership | Whether this invocation holds the transient runtime lock | Required before starting managed dependencies |
| application started | Whether `DictationService` successfully started | Must be false until all required readiness checks pass |

### State Transitions

```text
starting -> waiting_ready -> ready -> stopping -> stopped
starting -> stopping -> stopped
waiting_ready -> recovering -> stopping -> stopped
ready -> recovering -> stopping -> stopped
```

`recovering` is entered when an owned dependency exits or a required capability is lost after readiness. The invocation stops accepting dictation and emits only fixed content-free status before cleanup.

## Managed Dependency

Represents the local speech-recognition or cleanup dependency within one combined invocation.

| Field | Description | Validation |
| --- | --- | --- |
| name | Fixed dependency identifier: speech recognition or cleanup | Fixed non-content value |
| endpoint | Configured local endpoint used for readiness and inference | Must pass existing loopback-only validation before launch or use |
| initial state | `preexisting` or `unavailable` based on initial probe | Set before any launch attempt |
| ownership | `preexisting` or `started_by_invocation` | Only `started_by_invocation` may be stopped by this invocation |
| process state | `not_started`, `starting`, `ready`, `failed`, or `stopped` | Transitions are monotonic except `failed` to `stopped` during cleanup |
| process handle | In-memory handle for a process launched by this invocation | Absent for pre-existing dependencies; cleared after stop |

### Rules

- A pre-existing dependency is never terminated, killed, reconfigured, or otherwise controlled by the combined invocation.
- A dependency launch failure, readiness timeout, or unexpected owned-process exit transitions the invocation to safe cleanup.
- A dependency endpoint that is non-local, authenticated, unsupported, or otherwise unsafe is rejected before launch and cannot become ready.

## Readiness Snapshot

A content-free result of the existing local checks.

| Field | Description | Validation |
| --- | --- | --- |
| speech recognition ready | Whether the local ASR health check passed | Required for ready |
| cleanup ready | Whether the configured local model is ready | Required for ready |
| microphone ready | Whether capture permission/device is available | Required for ready |
| trigger ready | Whether global push-to-talk can be registered | Required for ready |
| placement ready | Whether the platform can safely identify the insertion target | Required for ready |
| limitations | Fixed non-content reasons for optional unavailable capabilities | Cannot include user content |

The combined invocation reports ready only when every required field is ready and `DictationService.start()` succeeds.

## Runtime Lock

A transient local coordination record used only while a combined invocation is active.

| Field | Description | Validation |
| --- | --- | --- |
| owner identifier | Opaque identifier of the current invocation | Compared atomically when releasing |
| creation time | Operational timestamp | Used only to identify stale-lock recovery policy; contains no user content |

The lock is removed by the owning invocation in all normal, error, and interruption cleanup paths. Lock contention does not attach to, stop, or modify the existing invocation.

