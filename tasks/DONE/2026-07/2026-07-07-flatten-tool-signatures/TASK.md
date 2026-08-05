# TASK — 2026-07-07-flatten-tool-signatures
owner: Engineer
immutable: true

## Requirements
- R1: Flatten the three sub-agent tool signatures so the model-facing args schema
  is FLAT (top-level `prompt`, `max_results`/`file`) instead of a single opaque
  `request` wrapper object. This aligns the schema with the orchestrator system
  prompt (which says "Argument: `prompt`") and removes the meaningless `request`
  nesting that weak tool-callers (Gemma) mis-handle.
  - search_web(prompt, max_results=5)
  - analyze_document(prompt, file=None)
  - analyze_image(prompt, file=None)
- R2: Preserve per-parameter descriptions and validation bounds (min_length,
  ge/le) on the flat params via typing.Annotated + pydantic Field, so the model
  still sees what each argument means.
- R3: Behaviour must be unchanged end-to-end: file injection at dispatch still
  works, and each tool still returns the same AgentResponse envelope.

## Acceptance
- A1: Each tool's generated input schema has top-level `prompt` (+ `max_results`
  or `file`), NOT a nested `request` object.
- A2: File-consuming tools still receive the injected file; FileService.inject
  keeps working unchanged.
- A3: No behavioural change to providers or envelopes; all three modules
  py_compile clean.

## Constraints
- Touch only the three tool modules. Do NOT change FileService.inject (already
  flatten-tolerant), the providers, the schemas, or the orchestrator prompt.
