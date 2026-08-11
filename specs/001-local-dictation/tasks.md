# Tasks: Local Push-to-Talk Dictation

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/cli.md`, and `quickstart.md`

## Dependencies

`Setup → Foundations → P1 complete pipeline → P1 privacy/fidelity → P2 dictionary → P2 safe placement → P2 setup/devices → P2 context → P1 styles → platform validation → polish`.

## Phase 1: Setup

- [ ] T001 Create `pyproject.toml` for Python 3.11+ with only `sounddevice` and `pynput` runtime dependencies, plus the `dictate` CLI entry point.
- [ ] T002 Create the package skeleton in `src/dictate/` and `tests/{unit,integration,acceptance,fixtures}/` following `plan.md`.
- [ ] T003 [P] Add `unittest` discovery and a metadata-only logging configuration test in `tests/unit/test_privacy.py`.

## Phase 2: Foundations

- [ ] T004 Implement TOML preferences, direct text-dictionary parsing, safe atomic preference writes, and defaults in `src/dictate/config.py` and `src/dictate/dictionary.py`.
- [ ] T005 Implement the single-session state machine and memory-clearing terminal transitions in `src/dictate/session.py` with `tests/unit/test_session.py`.
- [ ] T006 Implement loopback-only endpoint validation and content-redacting operational logging in `src/dictate/privacy.py` with `tests/unit/test_privacy.py`.
- [ ] T007 Define the narrow platform adapter contract for target snapshots, context, permissions, hotkeys, and insertion in `src/dictate/platform/base.py`.

## Phase 3: P1 Complete Local Dictation Slice

**Goal**: Prove press → capture → local ASR → local cleanup → verified insertion.

- [ ] T008 Implement default-microphone in-memory PCM capture and press/release lifecycle in `src/dictate/audio.py` with `tests/unit/test_audio.py`.
- [ ] T009 Implement whisper-server supervision, readiness, in-memory request submission, and local ASR failures in `src/dictate/asr.py` with `tests/integration/test_whisper.py`.
- [ ] T010 Implement loopback Ollama cleanup using `urllib.request`, required model, `think: false`, deterministic options, bounded context, keep-alive, and transformed-text-only validation in `src/dictate/cleanup.py` with `tests/integration/test_cleanup_client.py`.
- [ ] T011 Implement generic `pynput` press/release monitoring and injection adapter in `src/dictate/platform/generic.py` with `tests/unit/test_generic_platform.py`.
- [ ] T012 Wire `dictate serve` orchestration in `src/dictate/service.py` and `src/dictate/cli.py`; require original target revalidation before insertion.
- [ ] T013 Add an offline end-to-end acceptance test for the complete pipeline in `tests/acceptance/test_offline_pipeline.py`.

## Phase 4: P1 Privacy and Faithful Cleanup

- [ ] T014 Add fixed cleanup corpus covering filler, false starts, technical terms, dictated questions, lists, and Natural/Formal/Casual/Technical output in `tests/fixtures/cleanup-corpus.json` and `tests/integration/test_cleanup_corpus.py`.
- [ ] T015 Add content-not-in-logs and no-persistent-artifact privacy regressions in `tests/acceptance/test_privacy.py`.
- [ ] T016 Add cleanup failure tests proving discarded content, no insertion, and content-free errors in `tests/integration/test_processing_failures.py`.

## Phase 5: P2 Dictionary and Safe Placement

- [ ] T017 Implement global/project dictionary discovery, merging, project-over-global precedence, and bounded ASR/cleanup term input with `tests/unit/test_dictionary.py`.
- [ ] T018 Implement in-process explicit recovery-result lifecycle and focus-change suppression in `src/dictate/service.py` with `tests/acceptance/test_focus_safety.py`.

## Phase 6: P2 Setup, Devices, and Failures

- [ ] T019 Implement `dictate setup`, `dictate doctor`, and `dictate devices` in `src/dictate/cli.py`, requiring all approved readiness capabilities and content-free remediation.
- [ ] T020 Implement explicit microphone selection, unavailable/disconnected/default-change failures, and tests in `src/dictate/audio.py` and `tests/integration/test_devices.py`.

## Phase 7: P2 Context and Styles

- [ ] T021 Implement bounded original-target context collection and permission failure handling in `src/dictate/context.py` with `tests/unit/test_context.py`.
- [ ] T022 Implement Natural default and Formal/Casual/Technical profile selection in `src/dictate/config.py` and cleanup prompt construction with `tests/unit/test_prompt.py`.

## Phase 8: Platform Refinement and Polish

- [ ] T023 Implement macOS adapter/permission diagnostics and validate press-release, context, target verification, and insertion on macOS in `src/dictate/platform/macos.py`.
- [ ] T024 Implement Windows adapter/permission diagnostics and validate equivalent outcomes on Windows in `src/dictate/platform/windows.py`.
- [ ] T025 Implement Linux adapter/permission diagnostics and validate equivalent outcomes on Linux in `src/dictate/platform/linux.py`.
- [ ] T026 Document installation, explicit local-runtime/model acquisition, configuration files, privacy behavior, and common diagnostics in `README.md`.
- [ ] T027 Run the quickstart acceptance matrix and record platform results without user content in `specs/001-local-dictation/quickstart.md`.

## Parallel Opportunities

After T002, T003 and T004 can proceed in parallel. After T007, T008, T009, T010, and T011 can proceed
in parallel. After T012, T014 and T015 can proceed in parallel. T023–T025 can proceed in parallel.

## Implementation Strategy

MVP is T001–T013: it includes local Ollama cleanup as part of the first vertical slice, not an optional
later enhancement. Then complete privacy/fidelity gates, dictionary and placement safety, operational
commands, bounded context/styles, and OS-specific refinement. Do not add GUI/TUI, cloud, telemetry,
databases, plugin/provider frameworks, or generalized backend abstractions.

