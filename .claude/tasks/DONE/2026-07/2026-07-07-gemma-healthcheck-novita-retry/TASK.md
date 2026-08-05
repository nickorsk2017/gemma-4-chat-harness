# TASK — 2026-07-07-gemma-healthcheck-novita-retry
owner: Engineer
immutable: true

## Requirements
- R1: `make gemma-check` fails with Novita 429 `server_overload`.
- R2: Retry the request up to 4 times with increasing backoff (2/4/8s).
- R3: Lower `max_tokens` 131072 -> 512: reserving 128K completion tokens makes the
  scheduler reject the request first under load; a healthcheck needs a short reply.

## Acceptance
- A1: Transient 429 no longer fails the check on first hit; retry progress on stderr.
- A2: Everything else (provider, model, messages, temperature, .env key) unchanged.

## Constraints
- Single file: `mcp/scripts/gemma_healthcheck.py`.
