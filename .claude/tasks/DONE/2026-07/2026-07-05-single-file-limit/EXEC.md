# EXEC — 2026-07-05-single-file-limit

## v1 (implements PLAN v1; 4 files)
- MessageInput.tsx: single-attachment semantics — no `multiple`, new pick replaces the
  current file, attach button stays enabled, copy updated (D1).
- chatService.ts: >1 file -> ChatServiceError before any fetch (D2).
- chat_service.py: save_uploads rejects len(files) > 1 with GatewayError; docstring
  reflects single-file context (D3).
- chatService.test.ts: + ">1 file rejected, no fetch" case (D4).
