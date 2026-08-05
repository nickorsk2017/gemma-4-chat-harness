# TASK — 2026-07-07-gemma-healthcheck-novita
owner: Engineer
immutable: true

## Requirements
- R1: Provider changed to Novita. Replace `mcp/scripts/gemma_healthcheck.py` with the
  Engineer-supplied snippet: openai SDK, base_url `https://api.novita.ai/openai`,
  model `google/gemma-4-31b-it`, system+user messages, max_tokens=131072,
  temperature=0.7, print first choice content.
- R2: API key must come from env `GEMMA_API_KEY` (the snippet's literal
  "GEMMA_API_KEY" is a placeholder), with the existing root-.env loader so
  `make gemma-check` keeps working.

## Acceptance
- A1: Script matches the snippet (client params, model, messages, max_tokens,
  temperature) with the key read from env/.env.
- A2: Non-zero exit + stderr message on failure.

## Constraints
- Single file: `mcp/scripts/gemma_healthcheck.py`.
