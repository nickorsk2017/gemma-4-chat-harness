# TASK — 2026-07-05-no-mock-file-upload-e2e
owner: Engineer
immutable: true

## Requirements
- R1 (no mock anywhere): remove every remaining mock: gateway MockOrchestratorClient and
  the "mock" orchestrator mode; compose mock defaults; doc_analyzer mock PDF extraction
  (replace with real pypdf); dead web_agent search/weather mock settings; stale mock
  wording in docs/examples/frontend header.
- R2 (frontend uploads): the chat composer accepts image (png/jpg/webp/gif) and PDF
  attachments. A non-empty text prompt is MANDATORY — files can never be sent without a
  prompt (UI enforces; gateway re-validates server-side).
- R3 (E2E path works): frontend -> gateway (multipart when files attached) -> gateway
  saves files to a volume shared with the mcp container and passes their container paths
  in `context` -> orchestrator's gemma planner routes pdf_path* to doc_analyzer and
  image_path* to image_analyzer with exact tool names/argument shapes -> results
  synthesized and returned to the chat.
- R4: GEMMA_API_KEY reaches the mcp container via compose; compose fails early if unset.
- R5: no hardcoded keys; existing layer rules respected (thin routers, contracts first,
  fail-soft envelopes, ui-kit without store access).

## Acceptance
- A1: zero matches for mock orchestration/extraction remnants in backend/, mcp/ source
  (MockOrchestratorClient, orchestrator_mode "mock", extract_provider, search_provider,
  weather_provider); backend Literal is ["stdio","http"].
- A2: pypdf extraction parses pages=None|"N"|"N-M" (unit-tested with a generated PDF if
  pypdf importable, else stub-tested logic).
- A3: gateway /api/chat/files (multipart) rejects: empty/whitespace prompt; disallowed
  file types; saves allowed files under settings.upload_dir; context carries
  pdf_path/image_path keys (stub runtime test).
- A4: planner prompt contains the full tool catalog with argument shapes and the
  context-path routing rule.
- A5: frontend: tsc --noEmit passes; jest suite (updated) passes; Send disabled when
  prompt empty even with files attached.
- A6: compose: mcp gets GEMMA_API_KEY (required syntax), shared uploads volume mounted in
  backend + mcp at /data/uploads, GATEWAY_ORCHESTRATOR_MODE=http, no mock defaults.

## Constraints
- No live LLM/network calls in validation. Follow subsystem CLAUDE.md layer rules.
