# VALIDATION — 2026-07-04-connect-chat-rest

## v1 — PASS

- R1/R4: `chatService.ts` reviewed against `gateway/schemas/chat.py` + `_common/schemas/response.py` —
  request `{prompt}` matches `ChatRequest` (context optional), envelope literals `"Success"/"Failed"`,
  `error_text` match exactly. Failed envelope / missing data / non-OK HTTP all throw; signal forwarded. ✔
- R2: base URL from `NEXT_PUBLIC_API_BASE_URL`, default `http://localhost:8000` (= gateway default port, CORS already allows :3000). ✔
- R3: signature unchanged; `tsc --noEmit` exit 0 (store/components compile untouched). ✔
- R5/A1: jest cannot run in the validation sandbox (darwin-arm64 SWC binary, linux host —
  environment limitation, not a code defect). Equivalent check: all 5 test cases executed via
  tsc-compiled standalone harness — ALL PASS. Engineer should run `npm test` on the host once (expected green).
- A2: manual smoke (gateway :8000 + `npm run dev`) left to Engineer — backend deps not installable in sandbox (no PyPI).
- A3: covered by Failed-envelope/HTTP-500 tests; store catch path unchanged.

No blocking issues. open_issues stays empty.
