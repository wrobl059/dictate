# Data Model

All content-bearing entities are in-memory only unless explicitly marked as preferences.

## Persistent preferences

- **Configuration**: TOML; selected input (`system-default` or device identifier), trigger, Natural/Formal/
  Casual/Technical style, local executable paths, loopback endpoints, model names, and bounded limits.
  Validation rejects non-loopback inference URLs and unknown styles.
- **Global dictionary**: newline-delimited local terms.
- **Project dictionary**: newline-delimited local terms associated with a detected project root. It overrides
  a conflicting global spelling only for that session.

## Ephemeral session

- **Target snapshot**: application ID, window/document identity, text-target identity, captured at press.
- **Bounded context**: target metadata, selection, and nearby excerpt. Never screen/OCR data; cleared at end.
- **Audio buffer**: PCM frames held only until ASR finishes or failure cleanup occurs.
- **Session state**: `idle → recording → recognizing → cleaning → validating-target → inserted | recovery |
  failed`. Cancellation/failure clears content and ends at `failed`.
- **Recovery result**: final text held in process memory only when original target verification fails; cleared
  after explicit use, replacement, timeout, or exit.
- **Diagnostic result**: content-free capability state, timing, and remediation only.

## Invariants

1. At most one session is not terminal.
2. Audio/transcript/context/prompt/output are never written to ordinary logs or persistent history.
3. Insertion requires an exact original-target match immediately before injection.
4. Setup readiness requires all required local capabilities, including destination-context access.

