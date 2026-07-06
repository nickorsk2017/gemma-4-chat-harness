# EXEC — 2026-07-05-no-mock-file-upload-e2e

## v1 (implements PLAN v1; 21 files)
MCP: orchestrate.py planner prompt = tool catalog + {"request":{...}} shapes + pdf_path*/
image_path* routing + "never invent paths" (M1); doc providers real pypdf extract with
_parse_pages(None|"N"|"N-M") (M2); doc config -extract_provider (M3); doc pyproject +pypdf
(M4); web_agent config -search_/-weather_ (M5); mcp/.env.example -EXTRACT_PROVIDER (M6).
Backend: settings Literal["stdio","http"] + upload_dir (B1); orchestrator_client
-MockOrchestratorClient, factory raises on unknown mode (B2); chat_service ALLOWED_TYPES/
MAX_FILE_BYTES/save_uploads/reply_with_files, prompt re-validated server-side (B3);
router POST /api/chat/files multipart fail-soft (B4); pyproject +python-multipart (B5);
backend/CLAUDE.md rule 6 "Always real", run docs updated (B6).
Compose: uploads volume in mcp+backend at /data/uploads; GEMMA_API_KEY required syntax;
GATEWAY_ORCHESTRATOR_MODE=http fixed; root .env.example -mock lines (C1, C2).
Frontend: types +files/attachments (F1); service JSON vs multipart branch + client-side
mandatory prompt (F2); store send(prompt, files?) + attachment names (F3); MessageInput
attach button/chips/hint, Send disabled without text (F4); MessageBubble attachment chips
(F5); ChatView wiring + header copy (F6); chatService/chatStore tests rewritten, service
now module-mocked in store tests (F7).

## v1.1 (validator-found fix + hygiene)
- gateway/services/__init__.py: dropped stale MockOrchestratorClient re-export (A1 catch).
- .gitignore: + uploads/ (local-dev attachment dir).
