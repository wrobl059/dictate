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
- [ ] T030 CRITICAL: macOS now implements verified original-target snapshot/revalidation and direct insertion for standard Accessibility fields plus Slack; Terminal is intentionally unsupported and fails closed. Implement equivalent verified placement for Windows and supported Linux desktop sessions, retaining local recovery whenever verification or insertion fails, per FR-002, FR-017, FR-018, SC-001, Constitution VI/VII (partial)
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

---

## Phase 7: User Story 6 - Install the Default Local Pipeline (Priority: P1) 🎯

**Goal**: A user explicitly invoking `dictate setup --install-dependencies` acquires or retains every
required component of the supported local default pipeline, receives content-free per-component outcomes,
and receives final readiness only after local verification succeeds.

**Independent Test**: With deterministic fake package, download, and local runtime sources, invoke the
installed command on a machine missing one or more default components. Verify ordered acquisition and
verification; rerun to verify retention; then simulate network, authorization, storage, unsupported-platform,
download, and post-acquisition verification failures to verify nonzero content-free outcomes and no ready
claim.

### Tests for User Story 6

- [X] T041 [P] [US6] Add failing ordered component-outcome, retention, interrupted-artifact cleanup, and content-free remediation tests for the injectable installer coordinator in `tests/unit/test_installer.py`.
- [X] T042 [P] [US6] Add failing round-trip, validation, atomic-write, and failed-install preservation tests for verified whisper executable/model preferences in `tests/unit/test_config_dictionary_session.py`.
- [X] T043 [P] [US6] Add failing macOS, Windows, and Linux acquisition-dispatch and unsupported/authorization/storage remediation tests in `tests/unit/test_platform_adapters.py`.
- [X] T044 [P] [US6] Add failing standard-library bootstrap tests proving only `setup --install-dependencies` repairs declared Python dependencies and all other commands remain non-mutating in `tests/unit/test_bootstrap.py`.

### Implementation for User Story 6

- [X] T045 [US6] Extend validated atomic preferences with verified local `whisper-server` executable and default speech-model paths in `src/dictate/config.py` to satisfy `tests/unit/test_config_dictionary_session.py` (depends on T042).
- [X] T046 [US6] Add the minimal platform-specific external-runtime acquisition contract and content-free documented-route/unsupported remediation implementations in `src/dictate/platform/base.py`, `src/dictate/platform/macos.py`, `src/dictate/platform/windows.py`, and `src/dictate/platform/linux.py` to satisfy `tests/unit/test_platform_adapters.py` (depends on T043).
- [X] T047 [US6] Create the injected, ordered dependency discovery/acquisition/temporary-artifact cleanup coordinator and content-free component-result model for Python dependencies, whisper.cpp runtime/model, and Ollama runtime/model in `src/dictate/installer.py` to satisfy `tests/unit/test_installer.py` (depends on T041, T045, T046).
- [X] T048 [US6] Extend local ASR/readiness composition so retained or acquired whisper executable/model paths are locally verified and the verified `whisper-server` command is reusable by service startup in `src/dictate/asr.py`, `src/dictate/readiness.py`, and `src/dictate/service.py` (depends on T047; do not duplicate T029's general production composition root or T032's non-installer capability boundaries).
- [X] T049 [US6] Create the standard-library-only explicit-install dispatcher in `src/dictate/bootstrap.py`, route `python -m dictate` through it in `src/dictate/__main__.py`, and route the console script through it in `pyproject.toml` to satisfy `tests/unit/test_bootstrap.py` (depends on T044, T047).
- [X] T050 [US6] Add the `setup --install-dependencies` parser branch, ordered content-free component output, bare-setup install recommendation, and final shared-readiness gating in `src/dictate/cli.py`; extend `tests/unit/test_cli.py` and `tests/unit/test_readiness_privacy.py` for flag scope, output/exit ordering, non-mutating bare setup, and non-blocking context limitations (depends on T047, T048, T049).
- [X] T051 [US6] Add deterministic local process/download integration coverage for whisper runtime/model and Ollama runtime/model verification without real downloads or package-manager invocation in `tests/integration/test_installer_local_components.py` (depends on T048, T050).
- [ ] T052 [US6] Add subprocess-level clean-install, idempotent-retention, partial/interrupted-install, and content-free acquisition-failure acceptance coverage in `tests/acceptance/test_setup_install_dependencies.py`; after T029, extend `tests/acceptance/test_local_clients_offline.py` with explicit install → external-network block → composed local service verification (depends on T029, T050, T051).

**Checkpoint**: `setup --install-dependencies` is independently testable with deterministic local fakes;
it never mutates the host without the explicit flag, never reports ready after any failed component or final
required readiness check, and normal post-install operation remains offline.

---

## Phase 8: Installer Documentation and Cross-Cutting Verification

- [ ] T053 Replace manual default whisper.cpp/Ollama installation steps with the verified explicit setup workflow, bare-setup behavior, default artifacts, remediation categories, and post-install offline guarantee in `README.md`, `specs/001-local-dictation/contracts/cli.md`, `specs/001-local-dictation/quickstart.md`, and `specs/001-local-dictation/platform-acceptance-matrix.md` (depends on T050, T052).
- [ ] T054 Run the installer unit, integration, acceptance, and existing offline/privacy regression suites; verify documentation commands and inspect command output, preferences, installer temporary locations, and logs for content-free behavior in `tests/unit/test_installer.py`, `tests/unit/test_bootstrap.py`, `tests/integration/test_installer_local_components.py`, `tests/acceptance/test_setup_install_dependencies.py`, and `tests/acceptance/test_local_clients_offline.py` (depends on T052, T053).

## Dependencies & Execution Order — Dependency Installer

- **US6 foundations**: T041–T044 can start in parallel; they define the observable installer contract before implementation.
- **Persistent/platform prerequisites**: T045 depends on T042; T046 depends on T043; both block the installer coordinator.
- **Core installer**: T047 depends on T041, T045, and T046. T048 and T049 then depend on T047; T048 also supplies the locally verified runtime handoff used by the CLI.
- **CLI and verification**: T050 depends on T047–T049. T051 depends on T048 and T050. T052 depends on T050 and T051, plus existing T029 only for the composed post-install `serve` proof.
- **Documentation/polish**: T053 depends on demonstrated executable behavior in T052; T054 is the final regression gate.
- **Non-duplication**: T029 owns the general production `serve` composition root; T032 owns general microphone/trigger/placement/context readiness; T035 owns broad production offline/privacy coverage. US6 reuses these seams and only adds installer-specific behavior and verification.

## Parallel Opportunities — Dependency Installer

- T041, T042, T043, and T044 can run in parallel because they create independent test modules.
- After their respective tests exist, T045 and T046 can run in parallel.
- After T047, T048 and T049 can run in parallel if their shared installer interface is stable.
- T051's deterministic local-component coverage can proceed while T029 completes the general production composition root; T052's composed-service assertion waits only on T029.

## Implementation Strategy — Dependency Installer MVP

1. Complete T041–T047 to obtain a deterministic, content-free installer that retains or acquires only the
   required default components.
2. Complete T048–T050 to expose the explicit command while preserving bare setup and ordinary commands as
   non-mutating and offline.
3. Validate the installer independently with T051 and the non-composed portions of T052.
4. Complete the composed post-install offline proof after T029, then publish documentation in T053 and run
   T054 as the final privacy/offline regression gate.

[US6]: #phase-7-user-story-6---install-the-default-local-pipeline-priority-p1-
