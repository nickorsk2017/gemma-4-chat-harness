# TASK — 2026-08-05-english-only-artifacts
owner: Engineer
immutable: true

## Requirements
- R1: Add an English-only language rule to the root `CLAUDE.md`.
- R2: The rule covers every file written into this repository: task artifacts
  (`TASK.md`, `PLAN.md`, `EXEC.md`, `VALIDATION.md`, `LOG.md`, string values in `STATE.yaml`),
  source code, identifiers, comments, docstrings, tests, commit messages and documentation.
- R3: The rule states explicitly that Engineer chat may be in any language, but anything
  persisted to a file is English-only — chat language never propagates into artifacts.
- R4: The rule states the enforcement consequence: non-English artifact content is a hard
  violation; the actor rewrites the artifact in English before advancing `stage`.
- R5: Remediation of the already-drafted Russian `TASK.md` of
  `2026-08-05-pii-redaction-orchestration` is out of scope of this task and is tracked
  separately by the Engineer.

## Acceptance
- A1: Root `CLAUDE.md` contains a dedicated language section satisfying R2–R4.
- A2: No other file is modified.
- A3: The new section itself is written in English and does not contradict
  `.claude/CLAUDE.md` (precedence: `.claude/` harness > root > subsystem).

## Constraints
- C1: Root `CLAUDE.md` only — single file, no new dependencies (LOW).
- C2: Additive edit; do not rewrite or reorder existing sections.
- C3: Do not weaken or restate the Prime Directive or the no-exceptions clause.
