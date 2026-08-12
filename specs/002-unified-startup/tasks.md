# Tasks: Unified Dictate Startup

**Input**: Design documents from `/specs/002-unified-startup/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`

**Tests**: Required by the project constitution and the feature's measurable outcomes. Write/extend each listed test before its corresponding implementation and confirm it fails for the intended missing behavior.

**Organization**: Tasks are grouped by user story so each increment is independently demonstrable once its dependencies are complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches separate files and has no incomplete prerequisite.
- **[US#]**: Maps the task to the user story in `spec.md`.
- Every task identifies an exact repository-relative file path.

---

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Establish deterministic test seams and retain the explicit-install boundary before lifecycle work begins.

- [ ] T001 [P] Add no-argument non-install bootstrap regression coverage in `tests/unit/test_bootstrap.py`
- [ ] T002 [P] Create fake clock, sleeper, process-handle, lock, dependency, readiness, service, and fixed-status-reporter fixtures for lifecycle tests in `tests/unit/test_startup.py`
- [ ] T003 [P] Create managed local-process fake tests for Whisper and Ollama boundaries in `tests/unit/test_local_clients.py`

**Checkpoint**: The test suite has deterministic seams for process lifecycle, readiness polling, and lock ownership without requiring real local runtimes.

---

## Phase 2: Foundational (Blocking Lifecycle Safety)

**Purpose**: Implement the reusable local-process and invocation-state primitives that every story depends on.

**⚠️ CRITICAL**: Complete this phase before starting user-story integration work.

- [ ] T004 Add failing managed-process lifecycle cases—start, liveness, bounded terminate/wait/kill, idempotent stop, and no external-process ownership—to `tests/unit/test_local_clients.py`
- [ ] T005 Refine the managed Whisper process boundary to use verified preferences and bounded idempotent cleanup in `src/dictate/asr.py`
- [ ] T006 Add a separate injected Ollama managed-process boundary, local launch command, liveness, and bounded idempotent cleanup in `src/dictate/cleanup.py`
- [ ] T007 Add failing runtime-lock acquisition, owner-aware release, and contention-no-management cases in `tests/unit/test_startup.py`
- [ ] T008 Implement transient runtime lock and invocation/dependency state records with no user-content fields in `src/dictate/startup.py`
- [ ] T009 Add failing loopback-before-launch, missing-artifact/executable, fixed-remediation, and no-installer-acquisition cases in `tests/unit/test_startup.py`
- [ ] T010 Implement fixed content-free status reporting plus pre-launch endpoint and installed-artifact validation in `src/dictate/startup.py`
- [ ] T011 Extend unsafe endpoint and readiness privacy regressions for the supervisor boundary in `tests/unit/test_readiness_privacy.py`

**Checkpoint**: Process ownership, local-only validation, lock isolation, explicit-install-only behavior, and content-free status reporting are reusable and covered before application startup is wired.

---

## Phase 3: User Story 1 - Start Dictate With One Command (Priority: P1) 🎯 MVP

**Goal**: A fully installed offline user runs `dictate` once; Dictate starts missing local Whisper/Ollama services, waits until every required capability is ready, then provides the normal dictation pipeline.

**Independent Test**: With installed fake local dependencies initially stopped, invoke the no-argument CLI, verify both dependencies launch and exactly one ready status is emitted only after full readiness, then complete a deterministic dictation interaction offline.

### Tests for User Story 1

- [ ] T012 [P] [US1] Add failing supervisor tests for probe-before-launch, launch-only-unavailable, ownership marking, shared 30-second polling deadline, full readiness gating, and ready-once output in `tests/unit/test_startup.py`
- [ ] T013 [P] [US1] Add failing no-argument dispatch and `serve` compatibility-alias tests while preserving setup, doctor, and devices branches in `tests/unit/test_cli.py`
- [ ] T014 [P] [US1] Add fake-loopback combined startup integration coverage for initially stopped and pre-existing dependencies in `tests/integration/test_unified_startup.py`
- [ ] T015 [P] [US1] Add offline one-command startup and deterministic insertion acceptance coverage with captured content-free terminal output in `tests/acceptance/test_unified_startup.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement combined invocation orchestration—initial probes, start-only-unavailable dependencies, ownership recording, shared deadline polling, and `DictationService` creation only after `check_readiness()` passes—in `src/dictate/startup.py`
- [ ] T017 [US1] Integrate service construction so dependency supervision remains outside `DictationService` while its existing push-to-talk pipeline remains unchanged in `src/dictate/startup.py`
- [ ] T018 [US1] Make no-subcommand `dictate` dispatch to the combined invocation and route `dictate serve` through the identical compatibility path in `src/dictate/cli.py`
- [ ] T019 [US1] Preserve `serve --recover` and all existing explicit setup/diagnostic command semantics after parser changes in `src/dictate/cli.py`
- [ ] T020 [US1] Extend verified local-component command integration coverage if the finalized process boundary needs retained runtime metadata in `tests/integration/test_installer_local_components.py`

**Checkpoint**: In an installed offline environment, bare `dictate` starts the required local services and normal Dictate workflow without manual server commands.

---

## Phase 4: User Story 2 - Receive Safe Startup Guidance (Priority: P2)

**Goal**: Missing, unsafe, permission-blocked, or never-ready prerequisites produce actionable, content-free non-ready outcomes and never trigger acquisition or accept dictation.

**Independent Test**: Individually simulate missing runtime/model, unsafe endpoint, readiness timeout, and permission failure; verify no ready state, no auto-installation, safe cleanup, and fixed remediation for each.

### Tests for User Story 2

- [ ] T021 [P] [US2] Add failing supervisor cases for launch failure, missing model/runtime, readiness timeout, permission/capability failure, unsafe endpoints, and no service start before complete readiness in `tests/unit/test_startup.py`
- [ ] T022 [P] [US2] Add integration coverage for partial startup failure cleanup and loopback-only rejection in `tests/integration/test_unified_startup.py`
- [ ] T023 [P] [US2] Add acceptance cases for missing prerequisite, denied capability, unsafe endpoint, offline socket blocking, and content sentinel exclusion from lifecycle output in `tests/acceptance/test_unified_startup.py`

### Implementation for User Story 2

- [ ] T024 [US2] Add bounded readiness-timeout handling and fixed content-free remediation mapping for dependency, model, permission, trigger, and placement failures in `src/dictate/startup.py`
- [ ] T025 [US2] Ensure all startup failure paths reject dictation, avoid installer/acquisition calls and exception-content output, and clean up only invocation-owned dependencies in `src/dictate/startup.py`
- [ ] T026 [US2] Present the supervisor's safe readiness/failure outcomes without leaking exception text or user content in `src/dictate/cli.py`

**Checkpoint**: Each unavailable or unsafe prerequisite produces an explicit, privacy-safe non-ready state with no partial usable Dictate service.

---

## Phase 5: User Story 3 - Stop the Combined Service Cleanly (Priority: P3)

**Goal**: Interrupting or failing a combined invocation stops only its Dictate service and locally owned dependencies, preserves pre-existing services, and safely handles concurrent invocations or owned dependency loss.

**Independent Test**: Start with one or both dependencies pre-existing and others stopped, run Dictate, interrupt or induce an owned-process exit, and verify reverse-order owned cleanup, pre-existing preservation, lock release, and content-free recovery status.

### Tests for User Story 3

- [ ] T027 [P] [US3] Add failing supervisor tests for reverse-order ownership cleanup on interrupt, startup failure, and application-start failure, plus pre-existing dependency preservation in `tests/unit/test_startup.py`
- [ ] T028 [P] [US3] Add failing lock-contention, lock-release, and owned-dependency-loss recovery tests in `tests/unit/test_startup.py`
- [ ] T029 [P] [US3] Add integration tests for interruption cleanup and pre-existing service preservation in `tests/integration/test_unified_startup.py`
- [ ] T030 [P] [US3] Add acceptance tests for interrupted startup, second invocation, runtime owned dependency loss, and content-free shutdown/recovery output in `tests/acceptance/test_unified_startup.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `finally`-based application-first and reverse-launch-order owned dependency cleanup with idempotent lock release in `src/dictate/startup.py`
- [ ] T032 [US3] Monitor owned dependency liveness after ready, transition to fixed content-free recovery, stop accepting dictation, and trigger owned cleanup in `src/dictate/startup.py`
- [ ] T033 [US3] Map terminal interruption and owned-dependency-loss outcomes to clean combined-invocation termination in `src/dictate/cli.py`

**Checkpoint**: Shutdown and failure never leave invocation-owned processes behind, never stop pre-existing processes, and never permit competing invocations to interfere.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update user guidance, protect regressions, and verify the documented end-to-end behavior.

- [ ] T034 [P] Replace obsolete manual Whisper/Ollama startup instructions and document bare `dictate`, `serve` compatibility, setup-only acquisition, local-only boundaries, and ownership semantics in `README.md`
- [ ] T035 [P] Update the existing command contract to describe bare-command combined startup and retained `serve` compatibility in `specs/001-local-dictation/contracts/cli.md`
- [ ] T036 Run the full unittest suite and resolve unified-startup regressions across `tests/`
- [ ] T037 Execute every scenario in `specs/002-unified-startup/quickstart.md` and record any platform-specific limitations in `specs/002-unified-startup/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 — Setup**: No dependencies; T001–T003 can run in parallel.
- **Phase 2 — Foundational**: Depends on setup test seams. T004 precedes T005–T006; T007 precedes T008; T009 precedes T010. T011 can run alongside other foundational test work.
- **Phase 3 — US1**: Depends on all foundational work. T012–T015 are first; T016–T019 follow the relevant failing tests; T020 follows the finalized executable/runtime contract.
- **Phase 4 — US2**: Depends on the US1 supervisor composition, but its failure-mode tests and implementation can proceed independently of US3.
- **Phase 5 — US3**: Depends on the US1 supervisor composition, but its cleanup/ownership work can proceed in parallel with US2 after US1 is complete.
- **Phase 6 — Polish**: Depends on the selected story phases being complete; T034 and T035 can run in parallel, then run T036 and T037.

### User Story Dependencies

- **US1 (P1)**: Requires Phase 2; delivers the MVP independently.
- **US2 (P2)**: Requires the US1 combined invocation only; it adds safe non-ready handling and does not require US3 cleanup monitoring.
- **US3 (P3)**: Requires the US1 combined invocation only; it adds lifecycle ownership, cleanup, and contention behavior and does not require US2 remediation presentation.

### Parallel Opportunities

- T001–T003 are independent setup tests.
- T005 and T006 can proceed in parallel after T004 establishes lifecycle expectations.
- T012–T015 can be written in parallel because they use distinct test files.
- Following US1, T021–T023 (US2) and T027–T030 (US3) can be developed in parallel across their separate test files.
- T034 and T035 are independent documentation updates.

## Parallel Example: User Story 1

```text
Task: "Add supervisor readiness/ownership tests in tests/unit/test_startup.py"
Task: "Add default dispatch and serve alias tests in tests/unit/test_cli.py"
Task: "Add fake-loopback lifecycle integration coverage in tests/integration/test_unified_startup.py"
Task: "Add offline one-command acceptance coverage in tests/acceptance/test_unified_startup.py"
```

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 and Phase 2 to establish safe local lifecycle primitives.
2. Complete T012–T020 for US1.
3. Validate the no-argument offline combined start and normal dictation path.
4. Demonstrate the MVP before adding enhanced remediation and lifecycle recovery.

### Incremental Delivery

1. Deliver US1: one command starts a fully installed local Dictate environment.
2. Deliver US2: failures remain non-ready, actionable, local-only, and content-free.
3. Deliver US3: cleanup, process preservation, concurrency safety, and runtime-loss recovery.
4. Finish documentation and full regression/quickstart validation.

## Notes

- `[P]` tasks use different files and have no incomplete task dependency.
- Existing `tests/integration/test_local_clients.py` remains regression coverage; `tests/unit/test_local_clients.py` is a new process-boundary unit suite.
- Keep all runtime-lock metadata transient and free of user content.
- Do not introduce a daemon attachment protocol, automatic dependency acquisition, cloud fallback, persistent user-content storage, or a GUI while implementing these tasks.

