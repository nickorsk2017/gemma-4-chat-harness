# VALIDATION — 2026-08-05-english-only-artifacts

## v1

result: PASS
issues: []

### Acceptance
| Id | Evidence | Verdict |
|---|---|---|
| A1 | Root `CLAUDE.md` L55-72: section `## Language — English only in files`. R2 covered by the three bullets (artifacts incl. `STATE.yaml` string values `last_error`/`open_issues[].ref`; source identifiers, comments, docstrings, log/exception messages, test names/fixtures; documentation, configuration, commit messages). R3 covered by para 2 ("Engineer chat may be in any language ... never propagates into artifacts", verbatim quoting explicitly not an exemption). R4 covered by para 3 (hard violation; producing actor rewrites in English before advancing `stage`). | PASS |
| A2 | `git diff -- CLAUDE.md` is a single additive hunk, +19 lines, no deletions. No other tracked source/config/doc file changed by this task; only this task's own `EXEC.md`, `STATE.yaml`, `LOG.md`, `VALIDATION.md` were written, which the Read/Write Matrix mandates. | PASS |
| A3 | Section text is entirely English. No conflict with `.claude/CLAUDE.md`: the harness defines no language rule, so this is additive, not overriding. Precedence line at the end of the root file is untouched. | PASS |

### Constraints
- C1: single file (`CLAUDE.md`), no dependency changes. PASS
- C2: inserted immediately before `## Subsystem rules`; no existing section rewritten,
  reordered or deleted (diff shows zero `-` lines). PASS
- C3: Prime Directive and the no-exceptions block are byte-identical; the new section adds
  a constraint and does not restate or weaken either. PASS
- R5: `2026-08-05-pii-redaction-orchestration` not touched — correctly out of scope. PASS

### Notes (not issues)
- The clause "an actor that finds non-English content in an artifact it may read raises it
  as a blocking issue instead of advancing" is deliberately actor-agnostic. The formal
  `open_issues` handoff is Validator-owned per `.claude/CLAUDE.md` Failure Routing; a
  Planner/Executor encountering the case has `ESCALATED` available. Not a contradiction,
  but if the Engineer wants a named mechanism per actor it needs a separate task.
- The working tree carries unrelated pre-existing modifications (`mcp/guardrails/*`, a
  `tasks/` -> `.claude/tasks/` relocation, `TODO.md` removal). They predate this task and
  are outside its scope; flagged only so the commit for this task is staged narrowly.
