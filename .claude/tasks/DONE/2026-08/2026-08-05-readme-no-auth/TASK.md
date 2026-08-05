# TASK — 2026-08-05-readme-no-auth
owner: Engineer
immutable: true

## Requirements
- R1: `README.md` MUST state plainly that the project is a demo and carries NO
  authentication and NO authorization: every endpoint is open to whoever can reach
  the port, and there is no notion of a user, session, or ownership of a thread.
- R2: The statement MUST name the practical consequence rather than only the missing
  feature: an exposed deployment lets any caller spend the LLM budget and read or
  delete any thread by its id.
- R3: The statement MUST be placed where a reader meets it before the Quick start
  instructions, not buried at the end of the file.
- R4: The wording MUST NOT promise a fix, a roadmap item, or a date.

## Acceptance
- A1: `README.md` contains the demo / no-auth statement above the Quick start section.
- A2: The statement covers both authentication and authorization, plus the R2
  consequence.
- A3: No other file is modified; no code, config, or dependency changes.
- A4: The file stays valid Markdown and English-only (root CLAUDE.md).

## Constraints
- Documentation only. Scope = README.md.
- No claim about rate limiting: that work is a separate open task and is not shipped.
