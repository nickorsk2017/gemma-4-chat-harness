# TASK — 2026-07-05-error-http-status
owner: Engineer
immutable: true

## Requirements
- R1 (overrides backend/CLAUDE.md rule 5, per Engineer): error responses must NOT be
  HTTP 200. Mapping: client/validation errors -> 400; orchestration/upstream failures ->
  502; unexpected exceptions -> 500. Success stays 200. The ApiResponse envelope shape on
  the wire is unchanged (body still {status, data?, error_text?}).
- R2: gateway distinguishes validation errors (empty prompt, bad file type/size/count)
  from orchestration failures via exception types.
- R3: frontend service parses the envelope on non-OK responses and surfaces error_text;
  the store shows the actual service error message instead of a generic string.
- R4: backend/CLAUDE.md rule 5 updated to document the new policy.

## Acceptance
- A1: (stub runtime) /api/chat/files-equivalent flows: empty prompt -> 400 envelope;
  bad file type -> 400; orchestration failure -> 502; unexpected -> 500; success -> 200.
- A2: chatService prefers envelope.error_text on non-OK; falls back to "HTTP <code>".
  Store error == thrown ChatServiceError message. tsc clean; jest cases updated (host-run).
- A3: py_compile clean; backend/CLAUDE.md documents the mapping.
