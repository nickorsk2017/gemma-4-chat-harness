# VALIDATION — 2026-07-05-no-mock-file-upload-e2e

## v1 — PASS (one logic issue found and fixed in-iteration)
Sandbox: no PyPI/npm registry; no live LLM calls (per constraint).

- A1 PASS: after fixing a stale re-export in gateway/services/__init__.py, zero matches
  for MockOrchestratorClient / extract_provider / search_provider / weather_provider /
  '"mock"' in backend+mcp Python; Literal["http","stdio"]; upload_dir present; 9 files
  compile.
- A2 PASS: _parse_pages(None|"2"|"1-3"|"4-99") correct incl. clamping; "0" raises.
- A3 PASS (stub runtime): empty prompt with files -> "prompt is required"; bad type and
  >15MB rejected; happy path persists pdf+2 images and produces context
  {pdf_path, image_path, image_path2} with correct suffixes.
- A4 PASS: planner prompt lists all 9 tools with {"request":{...}} shapes + pdf_path*/
  image_path* routing + "NEVER invent paths".
- A5 PARTIAL-ENV: `tsc --noEmit` PASS (types incl. rewritten tests). Jest is NOT runnable
  in this sandbox: node_modules built on darwin-arm64, @next/swc linux binary missing and
  npm registry blocked (403). MUST run `pnpm test` (or npm test) on the host before
  commit — recorded as residual verification, not a code defect.
- A6 PASS: uploads volume mounted in mcp+backend at /data/uploads; GEMMA_API_KEY required
  (compose fails early); GATEWAY_ORCHESTRATOR_MODE=http; no mock defaults anywhere;
  root .env.example has no mock values.

Residual risks (non-blocking): host-side jest run (above); gemma structured-output /
vision behavior on the live NVIDIA endpoint still needs one real smoke test; planner
quality depends on gemma following the tool catalog.
