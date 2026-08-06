# TASK — 2026-08-05-readme-guardrails-retry
owner: Engineer
immutable: true

## Requirements
- R1: `README.md` MUST document the `guardrails` MCP service: what it checks
  (prompt injection, sexual/drug content, PII — structured via regex/checksum,
  unstructured via LLM judgment), where it sits (`master_orchestrator` gates input,
  `doc_analyzer` gates ingested document text, `web_agent` output is gated,
  `image_analyzer` is not), its port (8200), and its fail policy (input path
  fail-closed, output path fail-open only after its retry ladder is exhausted).
- R2: `README.md` MUST document the retry behavior on the guardrails output-check
  call: exponential backoff bounded by both an attempt cap
  (`GUARDRAILS_RETRY_ATTEMPTS`) and a wall-clock deadline
  (`GUARDRAILS_OUTPUT_DEADLINE_S`), and that `check_input` is single-shot with no
  retry.
- R3: Content MUST be placed as a new section after "Architecture" and before
  "Repository structure", and the `guardrails` service MUST be added as a row in
  the existing Ports table.
- R4: Facts MUST match the shipped `docker-compose.yml` / `mcp/agent_core/guardrails.py`
  values, not superseded design defaults from earlier task EXEC.md files.

## Acceptance
- A1: New `## Guardrails` (or equivalently named) section exists between
  Architecture and Repository structure, covering R1 and R2.
- A2: Ports table includes a `guardrails` row (port 8200).
- A3: No other file is modified.
- A4: Valid Markdown, English-only (root CLAUDE.md).

## Constraints
- Documentation only. Scope = README.md.
- Do not restate the full env-var list from `.env.example`; name only the vars
  needed to explain the retry bound (`GUARDRAILS_RETRY_ATTEMPTS`,
  `GUARDRAILS_OUTPUT_DEADLINE_S`).
