# EXEC — 2026-08-05-readme-guardrails-retry
exec_version: 1

## v1

### Change
`README.md`: new `## Guardrails` section inserted between `## Architecture` and
`## Repository structure` (R3). Covers the `guardrails` MCP service (port 8200,
`check_input`/`check_output`), what it screens (injection, sexual/drug content,
structured PII via regex/checksum, unstructured PII via LLM judgment, redact vs
block) per R1, call-site coverage (`master_orchestrator`, `doc_analyzer`,
`web_agent` gated; `image_analyzer` not) per R1, and the fail policy: input path
fail-closed, output path retries with exponential backoff bounded by
`GUARDRAILS_RETRY_ATTEMPTS` and `GUARDRAILS_OUTPUT_DEADLINE_S`, fail-open only
after the ladder is exhausted, `check_input` single-shot with no retry, per R2.
Added a `guardrails` row (port 8200) to the existing Ports table (A2). Facts taken
from shipped `docker-compose.yml` / `mcp/agent_core/guardrails.py`, not superseded
EXEC.md design defaults from earlier guardrails tasks (R4).

### Scope
One file, docs only (A3). No code, config, dependency, or other task-artifact
changes.

### Verification
- A1: section present, positioned per R3, covers R1+R2.
- A2: Ports table has the `guardrails | 8200` row.
- A3: `git status --porcelain` shows README.md plus this task's own artifacts only.
- A4: valid Markdown, English-only.
