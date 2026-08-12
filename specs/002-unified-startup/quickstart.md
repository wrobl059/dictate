# Quickstart: Validate Unified Dictate Startup

## Purpose

Validate that a fully installed Dictate environment starts the local speech-recognition service, local cleanup service, and Dictate application with one command, while preserving offline, privacy, and lifecycle guarantees.

See [CLI contract](contracts/cli.md) for command and ownership semantics and [data model](data-model.md) for transient lifecycle state.

## Prerequisites

- Use a supported operating system with Dictate installed as a terminal command.
- Complete the explicit local dependency setup before this validation:

```bash
dictate setup --install-dependencies
```

- Confirm the command reports local components/models installed. Do not manually start the local speech-recognition or cleanup services for the primary scenario.
- For an offline check, disable network access after setup completes.

## Primary End-to-End Validation

1. Ensure the local speech-recognition and cleanup services are stopped.
2. Start Dictate:

```bash
dictate
```

3. Expect one content-free ready status within 30 seconds. No additional terminal commands should be required to start either dependency.
4. Hold the configured push-to-talk trigger, speak a deterministic test phrase, and release it.
5. Verify text is inserted by the normal Dictate workflow.
6. Interrupt the foreground command using the terminal's normal interrupt key.
7. Verify the Dictate application and both dependency services launched by this command have stopped.

Expected result: startup, dictation, and shutdown complete without Internet access, cloud fallback, or content-bearing lifecycle output.

## Pre-existing Dependency Validation

1. Start one or both compatible local dependency services before launching Dictate.
2. Run:

```bash
dictate
```

3. After ready status, interrupt Dictate.
4. Verify that each dependency that was already running remains available; verify that any dependency started by Dictate is stopped.

Expected result: dependency ownership is preserved exactly as defined in the [CLI contract](contracts/cli.md#ownership-rules).

## Failure and Safety Validation

Perform each scenario independently and capture only lifecycle output; use non-sensitive fixture data.

| Scenario | Action | Expected result |
| --- | --- | --- |
| Missing component/model | Make one required local component unavailable, then run `dictate` | Non-zero non-ready outcome with fixed remediation to `dictate setup --install-dependencies`; no acquisition occurs |
| Unsafe endpoint | Configure a non-loopback dependency endpoint, then run `dictate` | Immediate non-ready failure before dependency launch or dictation |
| Dependency never becomes ready | Cause a launched dependency to fail readiness | Non-ready timeout within 30 seconds; started dependencies are cleaned up |
| Interrupted startup | Interrupt while readiness is pending | All dependencies started by the invocation stop before exit |
| Permission failure | Deny microphone, trigger, or placement capability | Dictate never reports ready or accepts dictation |
| Second invocation | Leave one `dictate` invocation active, then invoke `dictate` again | The second invocation fails safely without launching, attaching to, or stopping the first invocation's services |
| Runtime dependency loss | Stop a dependency started by ready Dictate | Dictate enters content-free recovery, stops accepting new dictation, and cleans up owned services |

## Regression Checks

Run the project test suite after implementation:

```bash
python -m unittest discover -s tests
```

Expected result: existing installer, offline, privacy lifecycle, pipeline, focus-safety, and platform matrix tests remain green, and unified-startup tests cover no-argument dispatch, ownership, cleanup, timeout, lock contention, and content-free output.


