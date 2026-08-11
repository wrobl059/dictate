<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.0.1
- Modified principles: X. Maintainability (expanded readability and anti-cleverness guidance)
- Added sections: none
- Removed sections: none
- Follow-up TODOs: none
-->

# Dictate Constitution

## Core Principles

### I. Local-Only Operation (NON-NEGOTIABLE)

Normal dictation MUST operate without Internet access. Speech audio, transcripts, contextual
information, dictionary contents, AI prompts, and generated output MUST remain on the user's local
machine. The product MUST NOT provide automatic cloud fallback. Network access is permitted only
during explicit user-initiated setup or update operations to obtain software or models; it MUST NOT
be a requirement of normal dictation.

### II. Privacy by Architecture (NON-NEGOTIABLE)

The product MUST NOT persist raw audio, transcripts, contextual text, prompts, or generated output
by default, and MUST NOT log user content. Operational logs MAY contain only timing, status, size,
and error metadata. Telemetry is prohibited by default. Context collection MUST be bounded to the
minimum useful for transcription cleanup. Screen capture and OCR MUST NOT be part of the default
architecture.

### III. Lowest Reasonable Complexity

Implementations MUST prefer straightforward code and standard-library functionality where practical,
while minimizing runtime dependencies. Dependency-injection and plugin frameworks, databases,
message buses, internal web applications, and generalized abstractions MUST NOT be introduced unless
a concrete current requirement justifies them. Do not build abstractions for hypothetical future
implementations. External local inference programs MAY be orchestrated rather than embedded when
that materially reduces complexity.

### IV. Command-Line First

Dictate is not a GUI application. Its normal product MUST be a long-running CLI service with small
setup, configuration, and diagnostic commands. Electron, Tauri, Qt, browser-based interfaces, and
other GUI frameworks MUST NOT be introduced. A TUI framework MUST NOT be introduced unless a
concrete terminal interaction requirement establishes its need.

### V. Opinionated Defaults

A fresh installation MUST require as little configuration as reasonably possible and expose one
supported default dictation pipeline. Local speech recognition and local AI cleanup are standard
parts of that pipeline, not optional product features. Advanced configuration MAY exist, but users
MUST NOT be required to assemble the processing pipeline themselves.

### VI. Cross-Platform Core, Narrow Platform Boundaries

Dictate MUST support macOS, Windows, and Linux. The primary dictation pipeline MUST remain
platform-independent. Unavoidable platform-specific code—including hotkeys, accessibility and
context collection, permissions, and text insertion—MUST be isolated at explicit boundaries.
Platforms need not share identical low-level implementations.

### VII. Fast Interactive Behavior

The product MUST behave as an input method, not as a transcription application: holding the
configured push-to-talk key starts recording; releasing it ends recording and starts processing; and
completed text is inserted into the intended text field with minimal perceived delay. Correctness and
privacy take precedence over latency optimization.

### VIII. Faithful Transformation

Speech recognition MUST determine what the user said, while post-processing transforms that
transcript into useful written text. Cleanup MUST preserve meaning, MUST NOT answer dictated
content, MUST NOT introduce unsupported information, and MUST respect supplied terminology. User
dictionaries and local context MAY improve recognition and cleanup, but MUST NOT change intended
meaning.

### IX. Test Observable Behavior

Tests MUST emphasize externally observable behavior, data flow, privacy guarantees, failure
behavior, and integration boundaries. The test suite MUST demonstrate normal operation without
Internet connectivity and MUST include regressions preventing sensitive content from appearing in
logs or persistent artifacts. Prefer a small deterministic integration test over excessive mocking
when practical.

### X. Maintainability

The codebase MUST remain understandable by one developer and readable at a glance. Code MUST avoid
cleverness, implicit tricks, compressed expressions, and unnecessary indirection when a direct,
obvious implementation is practical. Prefer descriptive, verbose variable and function names over
abbreviations or names that require readers to infer meaning. Prefer a simple function to a class
hierarchy when state or polymorphism is unnecessary. Every new dependency or architectural layer
MUST have a concrete justification. Comments SHOULD describe behavior, intent, invariants, and
non-obvious decisions so that a maintainer can understand the code without reconstructing it from
context; comments MUST NOT merely restate syntax or become misleading as behavior changes.

## Architectural Constraints

All specifications, plans, tasks, and implementations MUST comply with these principles. A proposal
that would transmit user content, require network access for normal dictation, retain user content by
default, add prohibited UI architecture, or weaken faithful transformation MUST be rejected unless
this constitution is amended first. Any proposed complexity, dependency, persistent artifact, or
platform-specific code MUST document its concrete necessity and compliance with local-only privacy.

## Delivery and Verification

Every implementation plan and review MUST identify its data flow, storage behavior, logging
behavior, network behavior, and operating-system boundary behavior. Changes affecting dictation MUST
be verified in an offline scenario. Changes affecting logs or storage MUST verify that representative
sensitive audio-derived and contextual content is neither logged nor persisted by default. Failures of
local inference, permissions, hotkeys, context collection, or text insertion MUST fail safely without
cloud fallback or content disclosure.

## Governance

This constitution supersedes conflicting project practices and governs all future specifications,
plans, tasks, implementations, and reviews. A proposed amendment MUST document the reason, affected
principles, privacy and offline-operation impact, migration requirements, and verification updates.
Amendments require explicit project maintainer approval before dependent work proceeds.

Constitution versions use semantic versioning: MAJOR for backward-incompatible principle removals or
redefinitions, MINOR for new principles or materially expanded obligations, and PATCH for
clarifications and non-semantic wording changes. Each amendment MUST update the Last Amended date
and prepend a Sync Impact Report. Ratification date remains the original adoption date.

Reviews MUST verify compliance before merge. Any exception requires a documented, time-bounded,
maintainer-approved amendment; no implementation may silently bypass a non-negotiable principle.

**Version**: 1.0.1 | **Ratified**: 2026-08-11 | **Last Amended**: 2026-08-11
