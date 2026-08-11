# Tasks: Local Push-to-Talk Dictation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`

## Dependencies

`Setup → foundations/readiness → complete safe local pipeline → privacy/fidelity → dictionary → setup/devices/context → styles → platform matrix → polish`.

## Phase 1: Setup and Foundations

- [X] T001 Create `pyproject.toml` for Python 3.11+ with only `sounddevice` and `pynput`; `python -m dictate --help` exposes `setup`, `serve`, `doctor`, and `devices`.
- [X] T002 Create the package/test skeleton described in `plan.md`; `unittest` discovers an empty passing suite.
- [X] T003 Implement TOML defaults, text dictionaries, atomic preference writes, and state transitions; unit tests prove Natural/default microphone/default trigger selection and content clearing on every terminal state.
- [X] T004 Implement shared readiness checks for local runtimes/models, microphone, trigger, placement, and optional context capability; unit tests distinguish required readiness failure from non-blocking context limitation.
- [X] T005 Implement loopback-only endpoint validation and metadata-only logging; unit tests prove non-loopback inference is rejected before content can be sent.
- [X] T006 Define the narrow platform adapter contract for target snapshots, optional context, permissions, hotkeys, insertion, and explicit recovery.

## Phase 2: P1 Complete Safe Local Dictation Slice

**Goal**: Prove press → target snapshot → in-memory audio → local ASR → local Ollama cleanup → target revalidation → insert or explicit recovery.

- [X] T007 Implement default-microphone in-memory PCM capture and press/release lifecycle; unit tests prove press starts capture, release stops it, and empty capture inserts nothing.
- [X] T008 Implement supervised loopback whisper-server with resident model and memory-backed ASR submission; integration tests prove readiness, successful local transcription, and content-free local failure.
- [X] T009 Implement loopback Ollama cleanup using the blessed model, `think: false`, deterministic options, bounded context, keep-alive, and output-only validation; integration tests prove transformed text is returned and no answer is generated.
- [X] T010 Implement generic `pynput` press/release monitoring, target snapshot, target revalidation, and injection; unit tests prove an unverified target never receives injected text.
- [X] T011 Implement in-process recovery: on unsafe placement retain one final result for `dictate serve --recover` to print once to stdout, clear it immediately after read/timeout/exit, and never use clipboard; acceptance tests prove this lifecycle.
- [X] T012 Wire `dictate serve` through the complete pipeline with an intentionally empty dictionary in this first slice; integration tests prove ASR and Ollama are both mandatory stages.
- [X] T013 Add focus-change acceptance coverage: begin in target A, change to B, prove B receives no text and recovery is required.
- [X] T014 Add an observable offline end-to-end acceptance harness that blocks all non-loopback socket connections for the service process while allowing required loopback runtimes; prove the full pipeline still inserts output.

## Phase 3: Privacy and Faithful Cleanup

- [X] T015 Add fixed cleanup corpus and regression tests for filler, false starts, terms, questions, lists, and all styles; expected outputs preserve meaning and never answer or invent content.
- [X] T016 Add privacy regressions with unique sentinels for transcript, context, dictionary terms, prompt, output, and recovery result; inspect logs, config, temp locations, and artifacts after success/failure/cancellation and prove no sentinel persists.
- [X] T017 [Conditional] Only if memory-backed whisper submission is proven unavailable, implement restrictive temporary-audio creation/deletion; tests prove deletion after success, ASR failure, cancellation, and process interruption. Otherwise document that no temporary-audio path exists.

## Phase 4: P2 Dictionary, Devices, Setup, Context, Styles

- [ ] T018 Implement global/project dictionary discovery and project-over-global precedence; unit tests prove dictionary terms reach both supported ASR prompting and cleanup prompt construction.
- [ ] T019 Implement `setup`, `doctor`, and `devices` using shared readiness checks; command tests prove required failures are nonzero, optional context is a non-blocking limitation, and remediation is content-free.
- [ ] T020 Implement explicit microphone selection and unavailable/disconnected/default-change failures; integration tests prove clear failure before recording.
- [ ] T021 Implement bounded original-target context and permission handling; unit tests prove only allowed fields are collected and unavailable context does not block dictation.
- [ ] T022 Implement Natural/Formal/Casual/Technical profiles; prompt tests prove style changes do not change substantive meaning.

## Phase 5: Platform Matrix, Latency, and Polish

- [ ] T023 Define the shared macOS/Windows/Linux acceptance matrix for trigger, microphone, permissions, optional context, target safety, insertion/recovery, and diagnostics; it permits different low-level implementations.
- [ ] T024 Validate macOS against the matrix and implement only required macOS adapter refinements; record pass/fail evidence without content.
- [ ] T025 Validate Windows against the matrix and implement only required Windows adapter refinements; record pass/fail evidence without content.
- [ ] T026 Validate Linux against the matrix and implement only required Linux adapter refinements; record pass/fail evidence without content.
- [ ] T027 Add warmed-model latency acceptance fixtures: fixed short audio, release-to-visible-placement clock, five-second threshold, and pass/fail reporting for each platform.
- [ ] T028 Document installation, explicit local model acquisition, defaults, privacy behavior, optional-context limitation, recovery command, and diagnostics in `README.md`.

## Parallel Opportunities

After T002, T003–T006 can proceed in parallel. After T006, T007–T010 can proceed in parallel. After T014,
T015 and T016 can proceed in parallel. T024–T026 can proceed in parallel after T023.

## Implementation Strategy

MVP is T001–T014 and includes local Ollama cleanup as a mandatory stage. Do not add GUI/TUI, cloud,
telemetry, databases, plugin/provider frameworks, or generalized backend abstractions.
