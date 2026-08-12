# Feature Specification: Unified Dictate Startup

**Feature Branch**: `002-unified-startup`  
**Created**: 2026-08-12  
**Status**: Draft  
**Input**: User description: "I need to be able to run dictate and all of its dependencies with one command. So, if I run the command \"dictate\" in my terminal, it should run the whisper server, the ollama server, and it should serve the dictate application all at once."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Start Dictate With One Command (Priority: P1)

A user whose required local components and models have already been installed runs `dictate` and receives a ready-to-use dictation service without separately starting the local speech-recognition service or local cleanup service.

**Why this priority**: This is the requested primary experience and removes the multi-terminal startup burden that prevents routine use.

**Independent Test**: In an environment with the required local components stopped but installed, run `dictate`, verify that the speech-recognition service, cleanup service, and Dictate service become ready, then complete a dictation interaction.

**Acceptance Scenarios**:

1. **Given** all required local components and models are installed and none is running, **When** the user runs `dictate`, **Then** it starts the required local speech-recognition and cleanup services and makes Dictate ready for dictation without further commands.
2. **Given** `dictate` has reported ready, **When** the user performs a normal dictation interaction, **Then** Dictate uses the locally available services and inserts the completed text through the normal workflow.
3. **Given** the terminal is offline, **When** the user runs `dictate` after completing setup, **Then** it becomes ready and performs normal dictation without network access or cloud fallback.

---

### User Story 2 - Receive Safe Startup Guidance (Priority: P2)

A user who runs `dictate` before required components, models, permissions, or local services are ready receives a clear, content-free explanation and the next action to take.

**Why this priority**: One-command startup must not hide prerequisites or leave users with a partially usable service.

**Independent Test**: Remove or make unavailable one prerequisite, run `dictate`, and verify that it reports the unavailable prerequisite and exits without exposing dictated or contextual content.

**Acceptance Scenarios**:

1. **Given** a required component or model is not installed, **When** the user runs `dictate`, **Then** it does not download or install anything automatically and reports the explicit setup action required.
2. **Given** a required service starts but does not become ready, **When** the user runs `dictate`, **Then** it reports that Dictate is not ready, identifies the failed prerequisite without user content, and does not accept dictation.
3. **Given** microphone or accessibility permission is unavailable, **When** the user runs `dictate`, **Then** it reports the permission issue and does not claim that Dictate is ready.

---

### User Story 3 - Stop the Combined Service Cleanly (Priority: P3)

A user can stop the terminal command and know that Dictate and any local dependency services started for that invocation are shut down cleanly.

**Why this priority**: A combined startup command must have predictable ownership and cleanup so it does not leave accidental background work running.

**Independent Test**: Start `dictate` with all services initially stopped, stop it from the terminal, and verify that its Dictate service and both dependency services are no longer running.

**Acceptance Scenarios**:

1. **Given** `dictate` started all required services, **When** the user interrupts the command, **Then** Dictate stops accepting dictation and shuts down every dependency service it started.
2. **Given** startup fails after one or more dependency services have started, **When** Dictate exits, **Then** it shuts down the services it started during that attempt and reports a content-free failure.
3. **Given** a compatible required dependency service was already running before `dictate` was invoked, **When** the user stops `dictate`, **Then** Dictate leaves that pre-existing service running.

### Edge Cases

- A dependency executable is installed but cannot be launched because of an invalid local configuration, unavailable port, or operating-system restriction; Dictate reports the affected prerequisite and exits without starting a partial dictation service.
- A dependency process exits or becomes unresponsive after Dictate is ready; Dictate stops accepting new dictation, reports a content-free recovery state, and never sends content to a remote fallback.
- Two `dictate` invocations are started at the same time; the later invocation must not interfere with the ready service or shut down services owned by the other invocation.
- The user interrupts startup while readiness checks are in progress; services started by the interrupted invocation are cleaned up before the command exits.
- A required local endpoint is not restricted to the local machine; Dictate treats the dependency as unsafe and does not make dictation ready.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Invoking `dictate` with no subcommand MUST start the Dictate application as a long-running terminal service.
- **FR-002**: Before accepting dictation, `dictate` MUST ensure that the required local speech-recognition service and local cleanup service are running and ready for use.
- **FR-003**: When either required dependency service is not already running, `dictate` MUST start it as part of the same command invocation.
- **FR-004**: `dictate` MUST report readiness only after Dictate, the speech-recognition service, and the cleanup service have each passed their applicable readiness checks.
- **FR-005**: Normal startup and dictation MUST operate without Internet access and MUST NOT use a cloud fallback.
- **FR-006**: `dictate` MUST NOT install, download, update, or otherwise acquire dependencies or models during normal startup; it MUST direct users to the explicit setup workflow when prerequisites are absent.
- **FR-007**: Startup, readiness, failure, and shutdown messages MUST not include raw audio, transcripts, context, prompts, generated text, or other user content.
- **FR-008**: If startup or a readiness check fails, `dictate` MUST not accept dictation, MUST provide a content-free reason and remediation, and MUST clean up dependency services that it started for that invocation.
- **FR-009**: When the user terminates a ready `dictate` invocation, it MUST stop the Dictate service and every dependency service started by that invocation.
- **FR-010**: `dictate` MUST not stop or alter a compatible dependency service that was already running before the invocation began.
- **FR-011**: All services used for normal dictation MUST be reachable only from the local machine; `dictate` MUST refuse an unsafe non-local dependency endpoint.
- **FR-012**: A second `dictate` invocation MUST either attach safely to a compatible ready service or fail with a clear content-free message; it MUST NOT disrupt services owned by another invocation.
- **FR-013**: The combined command MUST preserve the existing push-to-talk, local processing, target-safety, and text-insertion behavior once it reports ready.

### Key Entities

- **Combined invocation**: One user-launched `dictate` session that coordinates Dictate and the required local dependency services.
- **Dependency service**: A required local speech-recognition or cleanup service, including its readiness and ownership state.
- **Service ownership**: The relationship indicating whether a dependency service was started by the current combined invocation or was already running.
- **Readiness state**: The user-visible state showing whether all prerequisites are installed, locally reachable, permitted, and ready for safe dictation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tested fully installed offline environments, a user can start all required local services and reach a ready Dictate state using only the single command `dictate`.
- **SC-002**: In at least 95% of successful startup attempts on supported systems with local dependencies already installed, Dictate reports ready within 30 seconds of the command being entered.
- **SC-003**: In 100% of tested missing-prerequisite, permission-denied, and dependency-startup-failure cases, Dictate does not accept dictation and presents a content-free actionable failure message.
- **SC-004**: In 100% of tested user-interrupted and failed startups, services launched by that invocation are no longer running after the command exits, while pre-existing compatible services remain available.
- **SC-005**: In 100% of tested normal dictation sessions launched by the combined command, audio-derived and contextual content remains local and is absent from startup, readiness, and shutdown output.

## Assumptions

- The user has completed the explicit setup workflow before using `dictate`; setup is the only workflow permitted to obtain software or models.
- The existing product supports a local speech-recognition dependency and a local cleanup dependency, both of which are required for the default Dictate pipeline.
- A compatible service can be identified through its local readiness information without inspecting or transmitting user content.
- The terminal process remains the lifecycle owner for services it starts; the user stops the combined service through normal terminal interruption.
- This feature changes the default no-subcommand startup experience only; it does not add a graphical interface, cloud service, persistent dictation history, or new configuration surface.

