# Requirements Quality Checklist: Local Push-to-Talk Dictation

**Purpose**: Review privacy, offline behavior, interaction safety, and cross-platform requirements for
completeness, clarity, consistency, and observable acceptance criteria.
**Created**: 2026-08-11
**Feature**: [Local Push-to-Talk Dictation](../spec.md)

## Local-Only and Privacy Requirements

- [ ] CHK001 Are all normal-workflow data paths explicitly constrained to the local computer, including
  audio, transcript, context, dictionary terms, prompts, generated text, and recovery results?
  [Completeness, Spec §FR-008–FR-010]
- [ ] CHK002 Is “loopback-only inference” defined with an observable host-resolution rule and a failure
  outcome for a non-loopback configured endpoint? [Clarity, Plan §Technical Context]
- [ ] CHK003 Are retention requirements equally explicit for successful insertion, unsafe-placement
  recovery, failures, timeout, and service exit? [Coverage, Spec §FR-009, §FR-018]
- [ ] CHK004 Are the permitted operational-log fields exhaustively identified so “user content” cannot
  be interpreted differently by platform adapters? [Clarity, Spec §FR-010]
- [ ] CHK005 Is the offline acceptance environment defined well enough to distinguish a disconnected
  network from unavailable local models or processes? [Measurability, Spec §SC-001, §SC-004]

## Defaults and Push-to-Talk Semantics

- [ ] CHK006 Are first-run defaults specified for microphone, trigger, style, ASR model, cleanup model,
  context limit, and no-history behavior without requiring configuration choices? [Completeness, Spec
  §FR-003–FR-011; Plan §Technical Context]
- [ ] CHK007 Is “platform-appropriate” default trigger clarified for each OS as a behavioral capability
  rather than an assumption that macOS, Windows, and Linux share a key or hardware event? [Ambiguity,
  Spec §FR-002–FR-004]
- [ ] CHK008 Are press, hold, release, repeated press during processing, and release-before-audio
  behaviors each specified with observable state outcomes? [Coverage, Spec §FR-004, Edge Cases]
- [ ] CHK009 Is “recording begins immediately” quantified or bounded with an observable timing target?
  [Gap, Ambiguity]
- [ ] CHK010 Are requirements explicit about whether a trigger configuration change affects an active
  session or only the next session? [Clarity, Edge Cases]

## Destination Safety and Recovery

- [ ] CHK011 Is exact original-target verification defined independently for application, window, and
  text target, including what “verified” means on each supported OS? [Clarity, Spec §FR-017–FR-018]
- [ ] CHK012 Are requirements defined for an original target that remains visible but becomes read-only,
  destroyed, or changes document identity before insertion? [Gap, Edge Case]
- [ ] CHK013 Is explicit local recovery specified with a user-visible action, lifetime, and non-clipboard
  behavior, rather than only the subjective phrase “explicit recovery”? [Ambiguity, Spec §FR-018]
- [ ] CHK014 Are focus-change requirements consistent with the recovery-retention and no-content-history
  requirements? [Consistency, Spec §FR-009, §FR-018]

## Dictionary, Context, and Semantic Fidelity

- [ ] CHK015 Are dictionary parsing rules specified for comments, blank lines, case, duplicate terms,
  malformed entries, and project-root association? [Completeness, Spec §FR-014–FR-015]
- [ ] CHK016 Is project-over-global precedence defined for all conflicts, including multiple applicable
  project dictionaries and equal normalized spellings? [Coverage, Spec §FR-015]
- [ ] CHK017 Is the maximum count/size of ASR prompt terms and cleanup dictionary terms defined so
  “bounded” terminology input is objectively reviewable? [Ambiguity, Plan §Architecture]
- [ ] CHK018 Is “bounded nearby-text excerpt” quantified by a character/token limit and target-relative
  location, including selected-text precedence? [Ambiguity, Spec §FR-016]
- [ ] CHK019 Are context requirements clear about unsupported accessibility targets and whether setup’s
  required context capability conflicts with ordinary applications that expose no text context?
  [Consistency, Spec §FR-016, §FR-019]
- [ ] CHK020 Are semantic-fidelity requirements accompanied by criteria for acceptable filler removal,
  explicit correction resolution, and style changes without substantive alteration? [Clarity, Spec
  §FR-011–FR-013]
- [ ] CHK021 Is “never introduce new information” operationalized for punctuation, inferred subjects,
  list formatting, and terminology normalization? [Measurability, Spec §FR-012–FR-013]

## Device, Setup, and Cross-Platform Behavior

- [ ] CHK022 Are unavailable, disconnected, permission-denied, and default-device-changed microphone
  cases each specified with distinct user-facing outcomes? [Coverage, Spec §FR-005–FR-006, §FR-021]
- [ ] CHK023 Is “usable microphone” defined with observable capture/readiness criteria rather than only
  device enumeration? [Ambiguity, Spec §FR-019]
- [ ] CHK024 Are macOS, Windows, and Linux permission/remediation requirements specified as equivalent
  outcomes while explicitly allowing different OS-specific instructions and low-level mechanisms?
  [Clarity, Spec §FR-002, §FR-019]
- [ ] CHK025 Are requirements defined for a platform where generic keyboard injection cannot safely
  insert text, without assuming identical fallback behavior on every OS? [Gap, Plan §Platform boundaries]
- [ ] CHK026 Is setup success’s all-capabilities rule reconciled with applications or platforms that
  cannot expose destination context, including a clear supported-scope outcome? [Conflict, Spec §FR-019]
- [ ] CHK027 Are setup/update network permissions clearly separated from the “offline normal dictation”
  promise, including behavior when explicit model acquisition is unavailable? [Clarity, Spec §FR-008,
  Assumptions]

## Observable Acceptance and Latency Criteria

- [ ] CHK028 Is the five-second visible-placement target defined with a common clock source, audio
  sample characteristics, and ready-machine conditions across operating systems? [Measurability, Spec
  §SC-002]
- [ ] CHK029 Are the 20-sample offline and focus-change acceptance sets specified with representative
  applications, target types, and pass/fail treatment for intentionally unsupported targets?
  [Completeness, Spec §SC-001, §SC-005]
- [ ] CHK030 Are requirements defined for latency/failure reporting that preserve the no-content-log rule
  while still making “minimal perceived delay,” “safe,” and “appropriate” objectively reviewable?
  [Ambiguity, Spec §FR-010, §FR-017, §FR-021]

## Notes

- This checklist evaluates the written requirements, not an implementation.
- Items marked `[Gap]`, `[Ambiguity]`, or `[Conflict]` identify areas to clarify before implementation
  tasks claim complete acceptance coverage.

