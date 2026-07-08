# PLAN — 2026-07-07-file-passthrough-rearch
plan_version: 1

## v1

### Design decision (approved by Engineer via clarification)
- File transport = base64 inline: FilePayload{filename, content_type, content_b64}.
- Conversation memory is KEPT (thread_id/history/delete_thread).
- Each analyzer collapses to ONE tool taking {prompt, file}.

### Data flow (new)
Frontend -> gateway /api/chat/files (multipart) -> base64 -> FilePayload
  -> orchestrator.orchestrate({prompt, file?, thread_id?})
  -> Gemma tool loop picks tool; orchestrator injects raw file into doc/image tool args
  -> sub-agent decodes file itself (doc: PyPDF->text->Gemma; image: b64 data-url->Gemma;
     web: no file, {prompt}->Tavily) -> AgentResponse envelope merged into one answer.
The model never carries file bytes: file arg is left empty by the model and injected at
dispatch (same pattern the old code used for document_text).

### Contract (agent_core, shared truth)
- NEW mcp/agent_core/files.py: FilePayload(BaseModel){filename, content_type, content_b64}
  + FileKind enum {DOCUMENT, IMAGE} + classify(content_type)->FileKind|None
  + decode_bytes() helper. Reused by orchestrator + both analyzers.
- Gateway mirrors the same shape in gateway/schemas/chat.py (backend cannot import mcp/,
  rule 7) as FilePayload with identical field names -> JSON-compatible over MCP.

### File-by-file
1. mcp/agent_core/files.py (NEW) — FilePayload, FileKind, classify(), IMAGE/PDF mime maps.
2. mcp/agent_core/__init__.py — export FilePayload/FileKind/classify (optional convenience).
3. backend/gateway/schemas/chat.py — add FilePayload; ChatRequest drops `context`, gains
   `file: FilePayload | None`.
4. backend/gateway/services/chat_service.py — remove _extract_pdf_text, upload_dir writes,
   ALLOWED image/pdf disk logic. process_uploads -> _to_file_payload: read bytes, validate
   type/size, base64-encode, return FilePayload. reply()/reply_with_files forward file.
5. backend/gateway/services/orchestrator_client.py — orchestrate(prompt, file, thread_id):
   request={prompt, file(dict|None), thread_id}. Drop `context`. Keep envelope parse +
   delete_thread. Remove "trash": _parse unchanged but simpler request build.
6. backend/_common/env/settings.py — remove upload_dir (no longer used).
7. mcp/master_orchestrator/schemas/http.py — OrchestrateRequest{prompt, file?, thread_id?}
   (import FilePayload from agent_core). Drop context.
8. mcp/master_orchestrator/tools/orchestrator.py — remove _capture_document/_inject_document
   /_DOC_KEYS document-text handling. Add file-type system hint (R5). Inject the raw file
   dict into file-consuming tool calls at dispatch. Keep thread memory (messages only).
9. mcp/master_orchestrator/tools/subagents.py — LoadedTools.file_tool_names (was
   doc_tool_names); flag tools from BOTH doc + image sub-agents as file-consuming.
10. mcp/master_orchestrator/config.py — add image_subagent; file_subagents set
    {doc_subagent, image_subagent}. Drop doc-text-only DOC_SUBAGENT semantics
    (keep name for the set). document_max_chars removed (no text carried here).
11. mcp/master_orchestrator/prompts/orchestrate.py — rewrite: 3 tools
    (search_web{prompt}, analyze_document{prompt,file}, analyze_image{prompt,file});
    instruct model to leave `file` empty (injected) and how the Document/Image hint works.
12. mcp/doc_analyzer/schemas/http.py — AnalyzeRequest{prompt, file: FilePayload}.
13. mcp/doc_analyzer/schemas/document.py — DocAnalysis{filename, answer}.
14. mcp/doc_analyzer/tools/doc_tools.py — single analyze_document tool.
15. mcp/doc_analyzer/tools/providers.py — analyze_document(prompt,file): PyPDF decode
    (file.decode_bytes) -> text -> LangChain prompt (SystemMessage+Human) -> Gemma -> answer.
16. mcp/doc_analyzer/prompts/analyze.py — single ANALYZE_DOC system prompt.
17. mcp/doc_analyzer/pyproject.toml — add pypdf dependency.
18. mcp/image_analyzer/schemas/http.py — AnalyzeImageRequest{prompt, file: FilePayload}.
19. mcp/image_analyzer/schemas/image.py — ImageAnalysis{filename, answer}.
20. mcp/image_analyzer/tools/image_tools.py — single analyze_image tool.
21. mcp/image_analyzer/tools/providers.py — analyze_image(prompt,file): b64 data-url from
    file.content_b64 -> HumanMessage[text+image_url] -> Gemma -> answer.
22. mcp/image_analyzer/prompts/vision.py — single ANALYZE_IMAGE prompt.
23. mcp/web_agent/schemas/http.py — SearchRequest{prompt, max_results?} (query->prompt).
24. mcp/web_agent/tools/web_tools.py — search_web uses request.prompt.
    tavily.search_web signature unchanged (query arg fed request.prompt).
25. backend/tests/test_uploads.py — rewrite to assert base64 FilePayload, no disk writes.
26. backend/tests/test_chat_thread.py — FakeClient.orchestrate signature (prompt,file,thread_id).

### Risks / notes
- langchain-mcp-adapters derives tool schema from FastMCP input; `file` must be Optional
  (default None) so the model can omit it and dispatch-injection fills it.
- Sub-agent providers keep with_structured_output where a schema is returned; DocAnalysis/
  ImageAnalysis are simple {filename, answer} so structured output stays cheap.
- Backwards-compat with the old context/document_text path is intentionally dropped (R1-R3).
