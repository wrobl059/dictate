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

- [X] T018 Implement global/project dictionary discovery and project-over-global precedence; unit tests prove dictionary terms reach both supported ASR prompting and cleanup prompt construction.
- [X] T019 Implement `setup`, `doctor`, and `devices` using shared readiness checks; command tests prove required failures are nonzero, optional context is a non-blocking limitation, and remediation is content-free.
- [X] T020 Implement explicit microphone selection and unavailable/disconnected/default-change failures; integration tests prove clear failure before recording.
- [X] T021 Implement bounded original-target context and permission handling; unit tests prove only allowed fields are collected and unavailable context does not block dictation.
- [X] T022 Implement Natural/Formal/Casual/Technical profiles; prompt tests prove style changes do not change substantive meaning.

## Phase 5: Platform Matrix, Latency, and Polish

- [X] T023 Define the shared macOS/Windows/Linux acceptance matrix for trigger, microphone, permissions, optional context, target safety, insertion/recovery, and diagnostics; it permits different low-level implementations.
- [X] T024 Validate macOS against the matrix and implement only required macOS adapter refinements; record pass/fail evidence without content.
- [X] T025 Validate Windows against the matrix and implement only required Windows adapter refinements; record pass/fail evidence without content.
- [X] T026 Validate Linux against the matrix and implement only required Linux adapter refinements; record pass/fail evidence without content.
- [X] T027 Add warmed-model latency acceptance fixtures: fixed short audio, release-to-visible-placement clock, five-second threshold, and pass/fail reporting for each platform.
- [X] T028 Document installation, explicit local model acquisition, defaults, privacy behavior, optional-context limitation, recovery command, and diagnostics in `README.md`.

## Parallel Opportunities

After T002, T003–T006 can proceed in parallel. After T006, T007–T010 can proceed in parallel. After T014,
T015 and T016 can proceed in parallel. T024–T026 can proceed in parallel after T023.

## Implementation Strategy

MVP is T001–T014 and includes local Ollama cleanup as a mandatory stage. Do not add GUI/TUI, cloud,
telemetry, databases, plugin/provider frameworks, or generalized backend abstractions.

## Phase 6: Convergence

- [ ] T029 CRITICAL: Implement the production composition root and `serve` lifecycle so `dictate serve` loads validated preferences, selects the current OS adapter, starts the default local microphone → resident whisper.cpp → blessed Ollama pipeline, and runs until interrupted; return nonzero, content-free actionable errors for startup failures per FR-001, FR-004, FR-007, Constitution IV/V/VII (missing)
- [ ] T030 CRITICAL: Implement verified original-target snapshot, immediate revalidation, and direct text insertion for macOS, Windows, and supported Linux desktop sessions; fail closed with explicit local recovery when verification or insertion fails, and isolate each OS mechanism in its adapter per FR-002, FR-017, FR-018, SC-001, Constitution VI/VII (missing)
- [X] T031 Make `DictationService` return to a fresh IDLE session after successful insertion, recovery handoff, empty capture, processing failure, cancellation, and stop; add observable repeated-dictation, release-without-press, trigger-conflict, and mid-recording failure tests per FR-004, FR-009, FR-021, US1/AC1 (partial)
- [ ] T032 Implement concrete, metadata-only readiness boundaries and functional `setup`, `doctor`, and `devices` commands that verify loopback ASR/model availability, default/selected microphone availability, trigger registration/permission, placement permission, and optional context remediation; make required failures nonzero and cover permission/device/runtime failure paths per FR-005, FR-006, FR-019, FR-020, FR-021, SC-006 (missing)
- [ ] T033 Wire global and target-applicable project dictionary discovery into the production service, pass the bounded merged terms to both local ASR and cleanup, and report malformed or duplicate dictionary entries without corrupting either source; implement target-local bounded optional context collection only where the original target/permission permit it per FR-014, FR-015, FR-016, US4/AC1–3 (partial)
- [ ] T034 Validate the blessed `qwen3:4b-instruct-2507-q4_K_M` cleanup pipeline against a fixed real local-model corpus for all Natural/Formal/Casual/Technical profiles, including filler, corrections, terminology, questions, paragraphs, and lists; add enforceable handling for empty, answer-like, or non-faithful cleanup output without persisting content per FR-011, FR-012, FR-013, SC-003, Constitution VIII (partial)
- [ ] T035 Add production-boundary offline/privacy acceptance coverage that runs the composed service with external connectivity blocked while using actual loopback ASR/Ollama clients, then inspects ordinary logs, configuration, temporary locations, crash/failure paths, and service exit for sensitive sentinels; prove no cloud fallback or content persistence per FR-008, FR-009, FR-010, FR-021, SC-004, Constitution I/II/IX (partial)
- [ ] T036 Replace the non-functional separate-process `serve --recover` claim with an explicit, local, CLI-compatible recovery interaction available from the running service; preserve one result only after unsafe placement, clear it after explicit use/timeout/exit, and test the real command/service interaction per FR-018, T011 (partial)
- [X] T037 Harden default and explicitly selected microphone handling: preflight the exact session device, surface permission/disconnection/callback failures before or during recording as content-free failures, discard partial audio, and cover default-device changes plus unavailable-device behavior per FR-005, FR-006, FR-021, US5/AC2–3 (partial)
- [ ] T038 Perform and record content-free macOS host validation for the full composed offline pipeline: trigger hold/release, default and unavailable microphone, required permissions/remediation, target verification/insertion/recovery, context limitation, 20 focus changes, and 20 warmed latency runs per FR-002, SC-001, SC-002, SC-005, SC-006, plan: platform matrix (missing)
- [ ] T039 Perform and record content-free Windows host validation for the full composed offline pipeline: trigger hold/release, default and unavailable microphone, required permissions/remediation, target verification/insertion/recovery, context limitation, 20 focus changes, and 20 warmed latency runs per FR-002, SC-001, SC-002, SC-005, SC-006, plan: platform matrix (missing)
- [ ] T040 Perform and record content-free Linux host validation for the full composed offline pipeline: trigger hold/release, default and unavailable microphone, required permissions/remediation, target verification/insertion/recovery, context limitation, 20 focus changes, and 20 warmed latency runs per FR-002, SC-001, SC-002, SC-005, SC-006, plan: platform matrix (missing)
