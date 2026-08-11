# Platform Acceptance Matrix

This matrix defines the same observable contract on macOS, Windows, and Linux. The implementation may use different native mechanisms only when the generic `pynput` route is demonstrably insufficient. Every diagnostic and evidence record is metadata-only: it must never contain audio, transcript, context, prompts, dictionary entries, or generated text.

## Required matrix

| Capability | macOS | Windows | Linux | Common acceptance result |
|---|---|---|---|---|
| Trigger | Generic held-key monitoring | Generic held-key monitoring | Generic held-key monitoring | Key-down begins one session; matching key-up releases it; repeated key-down does not duplicate a session. |
| Microphone | OS default or selected input | OS default or selected input | OS default or selected input | A missing, disconnected, or unavailable input is a content-free readiness failure before recording. |
| Default dependency installation | Documented macOS runtime acquisition route | Documented Windows runtime acquisition route | Documented Linux runtime acquisition route | Only `setup --install-dependencies` may acquire missing default local dependencies. It retains verified components, verifies acquired artifacts, and reports an actionable content-free unsupported/authorization/storage/network remedy rather than silently selecting a package manager or cloud fallback. |
| Permissions | Microphone and Accessibility remediation | Microphone/input and accessibility remediation | Microphone/input and desktop-accessibility remediation | Required permission failure is nonzero/not-ready and names an OS-appropriate remedy without user content. |
| Destination context | Optional Accessibility-backed context | Optional accessibility-backed context | Optional desktop-accessibility-backed context | Its absence is a limitation, never a block to ordinary context-free dictation and never a reason to broaden collection. |
| Target safety | Original application/window/text target | Original application/window/text target | Original application/window/text target | Snapshot at key-down; exact revalidation immediately before insertion; any mismatch inserts nowhere. |
| Insertion/recovery | Native Accessibility replacement for verified standard fields; Quartz Unicode key events for verified Slack fields; Terminal unsupported | Unavailable pending a verified target mechanism | Unavailable pending a verified target mechanism | A supported placement route revalidates before direct injection; verification or insertion failure retains one in-process recovery result only; no clipboard or file fallback. |
| Diagnostics | `setup`/`doctor` remediation | `setup`/`doctor` remediation | `setup`/`doctor` remediation | Content-free required failures and optional limitations; no cloud fallback. |

## Current evidence — 2026-08-11

| Platform | Trigger contract | Microphone/permission diagnostics | Optional context | Target safety/insertion/recovery | Evidence | Result |
|---|---|---|---|---|---|---|
| macOS | Right Option release accepts both side-specific and generic macOS Alt release events | Native TCC probe requests Microphone permission without opening or retaining audio; denied/unavailable states report remediation | Reported as non-blocking limitation | Native Accessibility captures application/window/editable-field identity and revalidates it before placement. Address bars and Gmail-style editable/combo-box fields use Accessibility replacement; Slack uses verified Quartz Unicode events; Terminal is unsupported and fails closed. | `tests.unit.test_hotkey`; `tests.unit.test_platform_adapters`; `tests.unit.test_pipeline`; `tests.acceptance.test_platform_matrix` | PASS for deterministic safety contract and verified Slack host behavior; further host validation remains required |
| Windows | Generic hotkey adapter is instantiable | Reports remediation when target verification is unavailable | Reported as non-blocking limitation | Fails closed: no target snapshot and no insertion until a verified target mechanism exists; recovery instruction is available | `tests.unit.test_platform_adapters`; `tests.acceptance.test_platform_matrix` | PASS for safe common contract; automatic placement intentionally unavailable pending Windows-host validation |
| Linux | Generic hotkey adapter is instantiable | Reports desktop-session remediation when target verification is unavailable | Reported as non-blocking limitation | Fails closed: no target snapshot and no insertion until a verified target mechanism exists; recovery instruction is available | `tests.unit.test_platform_adapters`; `tests.acceptance.test_platform_matrix` | PASS for safe common contract; automatic placement intentionally unavailable pending Linux desktop-session validation |

The matrix test runs the same press/release, optional-context, focus-change, no-insertion, and memory-only recovery contract for every row. It uses deterministic non-user data and does not need local models, a microphone, or an external network connection.

## Warmed-model latency acceptance

Use the fixed 100 ms, 16 kHz mono signed-16-bit silence fixture in `tests/acceptance/test_platform_matrix.py`; it is deterministic synthetic data, not captured user audio. Start the resident local whisper.cpp process and warm the configured Ollama model via its local readiness request before timed runs. For each platform, perform 20 short dictations against a verified supported text target.

- Start the monotonic clock on trigger release.
- Stop it when verified insertion returns visible placement.
- Record only `platform`, sample number, duration in milliseconds, outcome category, and pass/fail.
- A successful sample passes only when it is visible within 5,000 ms.
- The platform passes when at least 90% of successful short samples pass. Failures remain content-free diagnostic outcomes and do not become cloud retries.

`PlacementTiming` and `tests.acceptance.test_latency` provide the release-to-placement clock seam and enforce the five-second threshold without recording content. Real-device results must be stored only as content-free project evidence, if retained at all.

