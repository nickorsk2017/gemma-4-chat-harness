# EXEC — 2026-07-07-file-passthrough-rearch
exec_version: 1

## v1 — implementation summary (per PLAN v1)

### New shared contract
- mcp/agent_core/files.py: FilePayload{filename, content_type, content_b64}, FileKind
  {DOCUMENT, IMAGE}, classify(content_type), decode_bytes(), data_url(), DOCUMENT_TYPES/
  IMAGE_TYPES maps. Exported from agent_core/__init__.py.

### Gateway (decides nothing)
- schemas/chat.py: added mirror FilePayload; ChatRequest drops `context`, gains `file`.
- services/chat_service.py: removed _extract_pdf_text + upload_dir/disk writes; ctor now
  takes only the client; process_uploads -> FilePayload|None (validate type/size, base64).
- services/orchestrator_client.py: orchestrate(prompt, file, thread_id); request now
  {prompt, file(model_dump), thread_id}; dropped `context`. Fixed stale docstring ref.
- routers/chat.py: ChatService(build_orchestrator_client(settings)).
- _common/env/settings.py: removed upload_dir.

### Orchestrator (routes; never decodes)
- schemas/http.py: OrchestrateRequest{prompt, file?: FilePayload, thread_id?}.
- config.py: added image_subagent + file_subagents property; removed document_max_chars.
- tools/subagents.py: LoadedTools.file_tool_names flags doc+image tools.
- tools/orchestrator.py: removed document capture/injection; adds Document/Image system
  hint when a file is present; injects the raw file dict into file-tool args at dispatch;
  keeps thread message memory.
- prompts/orchestrate.py: rewritten for search_web/analyze_document/analyze_image;
  added file_hint() announcing the attached file's kind.

### Sub-agents (each {prompt, file} -> Gemma)
- doc_analyzer: AnalyzeRequest{prompt,file}; DocAnalysis{filename,answer}; single
  analyze_document tool; provider decodes PDF via pypdf then LangChain->gemma; single
  ANALYZE_DOC prompt; pyproject adds pypdf. Fixed stale "mock" comment.
- image_analyzer: AnalyzeImageRequest{prompt,file}; ImageAnalysis{filename,answer};
  single analyze_image tool; provider sends text+image_url data URL to multimodal gemma;
  single ANALYZE_IMAGE prompt.
- web_agent: SearchRequest.query -> prompt; search_web uses request.prompt.

### Tests
- backend/tests/test_uploads.py: rewritten to assert base64 FilePayload, no disk writes.
- backend/tests/test_chat_thread.py: FakeClient.orchestrate(prompt, file=None, thread_id).
