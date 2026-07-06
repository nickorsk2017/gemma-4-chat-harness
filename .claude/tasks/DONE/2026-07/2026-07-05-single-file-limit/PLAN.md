# PLAN — 2026-07-05-single-file-limit

## v1
D1. MessageInput.tsx: MAX_FILES -> single-file semantics: drop `multiple`; addFiles
    replaces state with the last picked file ([file]); attach button always enabled
    (replacement UX), title "Attach image or PDF (one file)".
D2. services/chatService.ts: if files.length > 1 -> ChatServiceError("Only one file...")
    before fetch.
D3. backend chat_service.py: in save_uploads/reply_with_files reject len(files) > 1 with
    GatewayError("only one file can be attached per message").
D4. Tests: chatService.test.ts + one case (>1 file rejected, no fetch). Store test
    unchanged (single file already).
Files: MessageInput.tsx, chatService.ts, chat_service.py, chatService.test.ts.
