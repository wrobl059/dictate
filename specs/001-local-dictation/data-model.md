# Data Model

All content-bearing entities are in-memory only unless explicitly marked as preferences.

## Persistent preferences

- **Configuration**: TOML; selected input (`system-default` or device identifier), trigger, Natural/Formal/
  Casual/Technical style, loopback endpoints, model names, bounded limits, and the verified local
  whisper-server executable and default speech-model paths. Validation rejects non-loopback inference URLs,
  unknown styles, and empty or non-local runtime locations. Runtime locations are written atomically only
  after successful component verification.
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
- **Dependency installation result**: one ordered, content-free outcome per required default component:
  Python dependencies, whisper.cpp runtime, whisper.cpp model, Ollama runtime, and Ollama model. Each
  outcome records its component identity, terminal status (`retained`, `acquired`, `failed`, or
  `unsupported`), and a content-free remediation when applicable. Outcomes are command-scoped and are not
  retained as a user-content history.

## Invariants

1. At most one session is not terminal.
2. Audio/transcript/context/prompt/output are never written to ordinary logs or persistent history.
3. Insertion requires an exact original-target match immediately before injection.
4. Setup readiness requires every required local capability; destination-context access is an optional
   limitation and never blocks context-free dictation.
5. Only `setup --install-dependencies` may create, replace, or download runtime/model artifacts. A
   component is retained only after a local usability probe; incomplete temporary artifacts are never saved
   as the configured runtime or model.

