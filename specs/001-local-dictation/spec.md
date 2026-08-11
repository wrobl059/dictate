# Feature Specification: Local Push-to-Talk Dictation

**Feature Branch**: `001-local-dictation`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "Build a privacy-first, cross-platform local dictation tool that behaves like a system-wide push-to-talk writing assistant."

## Clarifications

### Session 2026-08-11

- Q: When focus changes after dictation begins, when may the service automatically insert the completed text? → A: Insert only if the original application, window, and text target can still be verified immediately before insertion; otherwise do not insert and retain a local recovery result.
- Q: If local speech recognition or cleanup fails, what should happen to the audio-derived result? → A: Discard audio and unusable intermediate content, insert nothing, and report a content-free actionable failure.
- Q: What local destination context may be collected for a dictation session? → A: Collect only active application identity, active window/document identity, current selection, and a bounded nearby-text excerpt from the same original target; otherwise collect no context.
- Q: If the same spoken term has different spellings in the global and applicable project-specific dictionaries, which spelling takes precedence? → A: The applicable project-specific entry takes precedence for that dictation session; otherwise use the global entry.
- Q: When guided setup finishes, what must be true before it may report success? → A: Core dictation capabilities—local processing, microphone, global trigger monitoring, and safe text placement—are verified. Destination-context access is optional; setup reports its unavailability with remediation but normal dictation remains available without context.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dictate into the Active Field (Priority: P1)

A user starts the dictation service, focuses a text field in any supported application, holds the
configured global push-to-talk trigger while speaking, and releases it. The user receives polished
text in the same field without manually handling audio, a transcript, or a clipboard.

**Why this priority**: This is the primary product experience and independently delivers the core
value of hands-free local writing assistance.

**Independent Test**: With the service running and no network connection, hold and release the
trigger while a supported text field remains active; verify that the final text appears in that field
and no copy/paste step is needed.

**Acceptance Scenarios**:

1. **Given** the service is ready and a supported text field has focus, **When** the user holds the
   configured global trigger, speaks, and releases it, **Then** recording starts on key-down, ends on
   key-up, processing starts automatically, and polished text is placed in the original field.
2. **Given** the user has no network connection, **When** they complete a normal dictation,
   **Then** the dictation completes locally without a cloud fallback or a network requirement.
3. **Given** the configured trigger conflicts with platform behavior or is unavailable,
   **When** the user starts the service, **Then** the service explains the issue and does not record
   until a usable trigger is configured.

---

### User Story 2 - Trust Local Privacy (Priority: P1)

A privacy-conscious user can dictate sensitive content knowing that audio, transcripts, destination
context, cleanup instructions, and generated text remain on the computer and are not retained by
default.

**Why this priority**: Privacy and offline operation are non-negotiable product promises; without
them the product does not meet its purpose.

**Independent Test**: Perform a representative dictation while offline, inspect ordinary logs and
application-managed storage, and verify that dictated and contextual test content is absent.

**Acceptance Scenarios**:

1. **Given** the user dictates content containing a unique sensitive phrase, **When** processing
   finishes, **Then** the phrase is absent from ordinary operational logs and default persistent
   artifacts.
2. **Given** a network connection becomes unavailable during normal use, **When** the user dictates,
   **Then** the service continues its local workflow or reports a local-component failure without
   sending content or attempting a cloud fallback.
3. **Given** the service gathers destination context, **When** it prepares cleanup, **Then** it uses
   only bounded information related to the active target and keeps that information local.

---

### User Story 3 - Produce Faithful Polished Writing (Priority: P1)

A user dictates natural speech and receives readable prose with appropriate punctuation,
capitalization, paragraphs, and lists. The service removes ordinary filler and resolves explicit
false starts or self-corrections while retaining the meaning of what the user said.

**Why this priority**: Raw transcription alone does not deliver the promised writing-assistant
experience; faithful cleanup is essential to its value and safety.

**Independent Test**: Dictate a scripted sample with filler, an explicit correction, a list, and a
question; compare the output to the expected written form and verify that it neither answers the
question nor adds unsupported facts.

**Acceptance Scenarios**:

1. **Given** a dictation includes ordinary filler and an explicit self-correction, **When** cleanup
   completes, **Then** the resulting text omits the filler and reflects the corrected intent.
2. **Given** a user dictates a question, **When** cleanup completes, **Then** the output renders the
   dictated question but does not answer it.
3. **Given** a user selects a built-in writing style, **When** cleanup completes, **Then** style
   changes formatting and tone without changing substantive meaning or adding facts.

---

### User Story 4 - Use Local Vocabulary and Target Context (Priority: P2)

A user maintains directly editable local vocabulary for names, product terms, technical terms,
identifiers, acronyms, and project-specific words. The user can dictate into a relevant destination
and benefit from bounded local destination context and applicable vocabulary without exposing either
outside the computer.

**Why this priority**: Accurate terminology and appropriately formatted output materially improve
usefulness for professional dictation while preserving the privacy promise.

**Independent Test**: Add distinctive terms to global and project-specific dictionaries, dictate a
sample into a matching project destination, and verify their expected spellings are present in the
final local output.

**Acceptance Scenarios**:

1. **Given** a term appears in the user's local dictionary, **When** the user dictates that term,
   **Then** the final text uses the known spelling when the spoken input reasonably matches it.
2. **Given** a project-specific dictionary applies to the active target, **When** the user dictates,
   **Then** applicable project terms supplement rather than replace global dictionary terms.
3. **Given** destination-context access is unavailable or permission is denied, **When** the user runs
   setup, **Then** setup reports the limited enhancement and remediation, does not broaden collection,
   and normal dictation remains available without context.

---

### User Story 5 - Set Up and Diagnose the Service (Priority: P2)

A new user can run a guided command-line setup that checks local prerequisites, permissions, audio
input, and local processing. The user can list microphones, select a non-default device when needed,
and run diagnostics that explain failures without revealing dictated content.

**Why this priority**: A system-wide service needs clear installation, permissions, and recovery
paths before it can provide reliable daily use across supported operating systems.

**Independent Test**: On each supported operating system, complete setup using the default microphone,
then run device inspection and diagnostics with a deliberately unavailable microphone or denied
permission; verify actionable, content-free results.

**Acceptance Scenarios**:

1. **Given** a first-time user, **When** they run setup, **Then** it guides them through verifying
   required local components, local processing, microphone access, and keyboard capabilities with
   platform-appropriate permission guidance.
2. **Given** the operating system default microphone is available, **When** the user starts normal
   dictation without selecting a device, **Then** recording uses that microphone.
3. **Given** a selected microphone becomes unavailable, **When** dictation begins, **Then** recording
   is not started and the user receives an understandable device-specific failure.

---

### User Story 6 - Install the Default Local Pipeline (Priority: P1)

A new user can explicitly ask Dictate to acquire the dependencies required for its supported default
local pipeline, including the local speech-recognition runtime and model, the local cleanup runtime,
and its default cleanup model. The user does not need to find, download, and connect those required
components manually before using Dictate.

**Why this priority**: A complete, supported default pipeline is essential to a usable fresh
installation and fulfills the product's opinionated-defaults promise.

**Independent Test**: On a supported computer without one or more required default components, run
`dictate setup --install-dependencies`, approve any operating-system authorization when needed, and
verify that setup acquires missing components, retains usable existing components, and reports ready
only after the default local pipeline is verified.

**Acceptance Scenarios**:

1. **Given** a user explicitly runs `dictate setup --install-dependencies` and required components are
   missing, **When** the computer can access the required acquisition sources, **Then** setup acquires
   the supported local speech-recognition runtime and its default model, the supported local cleanup
   runtime, and Dictate's default cleanup model before performing readiness checks.
2. **Given** one or more required components are already installed and usable, **When** the user runs
   `dictate setup --install-dependencies`, **Then** setup retains those components and acquires only
   the missing or unusable required components.
3. **Given** the user runs `dictate setup` without the dependency-installation option, **When** a
   required component is missing, **Then** setup reports the missing component and how to request the
   built-in installation without acquiring software or models.
4. **Given** acquisition fails because of unavailable network access, unsupported platform capability,
   insufficient permissions, or a failed download, **When** setup finishes, **Then** it reports the
   affected component and an actionable content-free remedy, does not claim readiness, and does not
   attempt a cloud fallback for later dictation.

---

### User Story 7 - Prevent Misplaced Sensitive Text (Priority: P2)

A user begins dictation in one field but changes focus before processing finishes. The service avoids
typing confidential output into an unrelated destination and gives the user a deliberate, local way to
recover the result when safe placement cannot be confirmed.

**Why this priority**: Safe placement is necessary to protect privacy when system focus changes during
asynchronous processing.

**Independent Test**: Start dictation in one supported field, change focus to a different field before
processing completes, and verify that generated text is not silently typed into the new field and is
available for explicit recovery.

**Acceptance Scenarios**:

1. **Given** the original application, window, and text target can still be verified immediately before
   placement, **When** processing completes, **Then** the final text is inserted into that original
   target.
2. **Given** focus changes and safe placement cannot be determined, **When** processing completes,
   **Then** the service does not type into the new target and preserves the result only for explicit
   local recovery.

### Edge Cases

- The user releases the trigger before meaningful audio is captured; the service reports no usable
  dictation and inserts nothing.
- Microphone permission, keyboard monitoring, or text-placement permission is denied, revoked, or
  unavailable; the service explains the affected capability and does not silently degrade privacy.
- The selected or default microphone is disconnected during recording; recording ends safely and the
  user receives an understandable failure without retaining partial audio by default.
- Local recognition or cleanup is unavailable, fails, or produces no usable result; the service
  discards captured audio and unusable intermediate content, sends no data externally, inserts
  nothing, and provides a content-free actionable failure.
- The active application does not expose usable target identity or does not support text placement;
  the service does not broaden context collection and offers explicit local recovery where a result
  exists.
- A dictionary entry is malformed or duplicated; the service identifies the local configuration issue
  without corrupting either dictionary. A spelling conflict between an applicable project-specific
  entry and a global entry uses the project-specific spelling for that session.
- The user changes writing style, microphone, or trigger while a dictation is in progress; the active
  dictation completes or fails under its starting settings, and the new setting applies to later use.
- A dependency installation is interrupted or only partially completes; a later setup run identifies
  incomplete or unusable components, does not treat them as ready, and can safely resume acquisition.
- The computer cannot install a required component because the platform is unsupported, disk space is
  insufficient, required authorization is denied, or acquisition sources are unavailable; setup names
  the affected component, preserves usable existing components, and offers a content-free remedy.
- The default cleanup model or speech-recognition model is acquired but cannot be used locally; setup
  reports that verification failed and does not report the service as ready.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a long-running command-line dictation service as the primary
  user interface, plus command-line setup, diagnostics, audio-input inspection, and configuration
  operations; it MUST NOT require a graphical interface.
- **FR-002**: The system MUST support normal dictation on macOS, Windows, and Linux, with a
  platform-independent core workflow and platform-appropriate behavior for system integration.
- **FR-003**: The system MUST let users configure a globally usable push-to-talk trigger and MAY use
  platform-specific defaults where necessary.
- **FR-004**: The system MUST start recording on trigger key-down, stop recording on key-up, and begin
  local processing automatically after key-up.
- **FR-005**: The system MUST use the operating system's default available microphone without required
  configuration and MUST let users select an available audio input explicitly.
- **FR-006**: The system MUST provide a command that lists available audio inputs and MUST report an
  understandable failure when the selected or default input is unavailable or disconnected.
- **FR-007**: The system MUST recognize speech locally and transform the resulting transcript locally
  into polished written text as one supported default pipeline.
- **FR-008**: Normal dictation MUST function without Internet access. The system MUST NOT send speech
  audio, transcripts, destination context, dictionary contents, cleanup instructions, generated text,
  or derived user content outside the local computer, and MUST NOT use an automatic cloud fallback.
- **FR-009**: By default, the system MUST treat captured audio, transcripts, destination context,
  cleanup instructions, generated text, and dictation history as ephemeral. It MUST NOT maintain
  history of audio, transcripts, or cleanup inputs and outputs.
- **FR-010**: The system MUST NOT write user content to ordinary logs. Operational logging MAY include
  only timing, status, sizes, and error metadata.
- **FR-011**: The system MUST offer built-in Natural, Formal, Casual, and Technical writing styles,
  select Natural by default, and apply style only to cleanup and formatting rather than substantive
  meaning.
- **FR-012**: Cleanup MUST preserve the user's intended meaning; it MAY remove ordinary filler and
  resolve explicit false starts or self-corrections, and it MUST apply appropriate punctuation,
  capitalization, paragraphing, and list formatting when supported by the dictated content.
- **FR-013**: Cleanup MUST NOT answer dictated questions, invent facts, add substantive content, or
  alter supplied terminology beyond formatting necessary for the selected writing style.
- **FR-014**: The system MUST provide directly user-editable local global dictionary data for known
  names, product terms, technical terms, identifiers, acronyms, and project-specific vocabulary.
- **FR-015**: The system MUST allow applicable project-specific vocabulary to supplement the global
  dictionary without replacing or modifying it, and MUST use known spellings to improve final
  transcription. When an applicable project-specific entry conflicts with a global entry, the
  project-specific spelling MUST take precedence for that dictation session.
- **FR-016**: The system MAY collect local destination context only from the original dictation target
  and only when that target and required permission are available. It MUST be limited to active
  application identity, active window/document identity, the current selection, and a bounded
  nearby-text excerpt from that same target; it MUST otherwise collect no context. Collected context
  MUST remain local and ephemeral by default and MUST NOT use screen capture, OCR, or unrelated
  applications.
- **FR-017**: The system MUST insert completed text without a separate copy/paste workflow only when
  the original application, window, and text target can still be verified immediately before placement.
- **FR-018**: If the original application, window, or text target cannot be verified immediately before
  placement, including because focus changed, the system MUST NOT insert text into any destination and
  MUST preserve any generated result only for explicit local user recovery.
- **FR-019**: Setup MUST report success only after it verifies required local components and models,
  local processing, a usable microphone, global trigger monitoring, and safe text-placement capability.
  Destination-context access is optional: if unavailable, setup MUST report the limitation and
  platform-appropriate remediation without preventing normal dictation without context.
- **FR-019a**: When a user explicitly invokes `dictate setup --install-dependencies`, setup MUST
  acquire every missing or unusable dependency required by the supported default local pipeline. This
  includes the supported local speech-recognition runtime and its default model, the supported local
  cleanup runtime, and Dictate's default cleanup model.
- **FR-019b**: Dependency acquisition MUST be initiated only by the explicit dependency-installation
  option. Setup without that option MUST remain a verification and diagnostic operation and MUST
  explain how to request built-in acquisition when a required default component is missing.
- **FR-019c**: Before reporting readiness after dependency acquisition, setup MUST verify that every
  required acquired or retained component is usable in the local default pipeline. It MUST retain
  usable existing components and MUST NOT report readiness if any required component is missing,
  incomplete, unusable, or cannot be verified.
- **FR-019d**: If dependency acquisition cannot complete, setup MUST identify the affected component
  and provide content-free, actionable remediation for unavailable network access, unsupported
  platform capability, denied authorization, insufficient storage, or acquisition failure. It MUST
  preserve usable existing components and MUST NOT enable a cloud fallback for normal dictation.
- **FR-020**: Diagnostics MUST report actionable readiness and failure information without exposing
  audio, transcripts, destination context, cleanup instructions, or generated text.
- **FR-021**: The system MUST preserve normal dictation privacy and local-only behavior when a
  permission, device, recognition, cleanup, context, or placement operation fails; it MUST provide a
  content-free, understandable failure rather than disclose content or fall back to a network service.
  When recognition or cleanup fails or yields no usable result, it MUST discard captured audio and
  unusable intermediate content and MUST insert nothing.

### Key Entities *(include if feature involves data)*

- **Dictation session**: An ephemeral interaction beginning at trigger key-down and ending after final
  text is safely placed, explicitly recoverable, or discarded; includes the original target identity
  and status but does not imply default persistent history.
- **Audio input preference**: The user's choice of default-system or explicitly selected microphone,
  together with availability status.
- **Push-to-talk preference**: The globally monitored trigger and its platform-specific availability
  status.
- **Writing style**: A selected local cleanup and formatting preference; built-in values are Natural,
  Formal, Casual, and Technical.
- **Global dictionary**: Directly editable local vocabulary that applies to the user's dictation.
- **Project dictionary**: Directly editable local vocabulary associated with a relevant project or
  target that supplements global vocabulary.
- **Destination context**: Bounded, ephemeral local information about the active dictation target used
  only to improve recognition and formatting.
- **Recovery result**: Locally retained generated text awaiting an explicit user action after safe
  automatic placement could not be determined.
- **Diagnostic result**: Content-free status and actionable remediation information for prerequisites,
  permissions, audio inputs, keyboard integration, local processing, and placement capability.
- **Dependency installation result**: Content-free status for each required default component,
  including whether it was retained, acquired, verified, or needs user remediation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an offline acceptance test with all required local components ready, a user completes
  95% of 20 scripted push-to-talk dictations from key-down through final text placement without a
  manual copy/paste step.
- **SC-002**: In the same offline test, at least 90% of successful short dictations produce final text
  within 5 seconds of trigger release, measured from the user's release to visible placement.
- **SC-003**: For a scripted set of 20 samples containing filler, explicit corrections, questions,
  terminology, paragraphs, and lists, reviewers confirm that 100% of outputs do not answer dictated
  questions or introduce unsupported substantive facts.
- **SC-004**: In privacy regression tests containing unique audio-derived, contextual, and generated
  markers, 100% of inspected ordinary logs and default persistent artifacts contain none of those
  markers.
- **SC-005**: In 20 focus-change tests where safe placement cannot be confirmed, 100% of generated
  results are withheld from the newly focused unrelated field and made available only through explicit
  local recovery.
- **SC-006**: On macOS, Windows, and Linux, a new user can complete guided setup, identify an available
  microphone, and obtain an actionable diagnostic result for a denied permission or unavailable device
  without exposing user content.
- **SC-007**: On macOS, Windows, and Linux test environments where supported acquisition sources are
  available, 100% of clean-install test runs can use `dictate setup --install-dependencies` to obtain
  and verify the supported default local pipeline without manually downloading or configuring its
  required local runtimes or models.
- **SC-008**: In 20 installation tests with a pre-existing usable required component, setup preserves
  that component and completes readiness verification without requiring its manual reinstallation in
  100% of runs.
- **SC-009**: In 20 simulated acquisition-failure tests, 100% of results identify the affected
  component, provide an actionable content-free remedy, and do not report Dictate as ready.

## Assumptions

- The first release supports one active dictation session at a time and targets text fields in
  applications that allow the operating system's supported text-placement mechanisms.
- Normal operation has all required local components and models installed during explicit setup or
  update. `dictate setup --install-dependencies` is the supported way to obtain the default required
  local runtimes and models; obtaining them may require network access only when the user explicitly
  initiates it.
- The supported default local pipeline has one documented default speech-recognition model and one
  documented default cleanup model. Users may still install or configure non-default components through
  future advanced workflows, which are outside this feature's dependency-installation scope.
- Users running dependency installation have sufficient disk space and can grant any required
  operating-system authorization. When either condition is not met, setup reports remediation rather
  than bypassing platform protections.
- Natural is the default style; built-in styles are available immediately, while user-defined custom
  styles are a future extension and are not required for this feature.
- The default microphone is the operating-system default at the start of a session. An explicit device
  selection is retained as a user preference without retaining dictated content.
- Local recovery is an explicit, user-controlled action and is designed to avoid placing generated
  text into an unrelated field; its precise interaction is deferred to planning as long as it remains
  command-line compatible and local-only.
- Destination-context access is an optional enhancement. When it is unavailable, unsupported, or denied,
  setup reports platform-appropriate remediation, normal dictation continues without context, and the
  service does not broaden collection to compensate.
- The stated success-criterion sample sizes and latency target are initial acceptance thresholds that
  may be refined during planning only if privacy, correctness, and offline operation are preserved.

