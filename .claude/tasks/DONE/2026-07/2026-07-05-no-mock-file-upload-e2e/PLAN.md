# PLAN — 2026-07-05-no-mock-file-upload-e2e

## v1

### MCP (6 files)
M1. master_orchestrator/prompts/orchestrate.py — rewrite PLANNER_SYSTEM: full tool catalog
    with EXACT argument shapes (every subtask's arguments = {"request": {...}}):
    web_agent: get_news{query,limit}, get_weather{location}, fetch_url{url};
    doc_analyzer: extract_text{path,pages?}, summarize_document{path,max_points},
    ask_document{path,question}; image_analyzer: describe_image{path},
    detect_objects{path,min_confidence}, ocr_image{path,lang}.
    Routing rule: context keys pdf_path/pdf_path2.. -> doc_analyzer with that exact path
    (Q&A if prompt asks a question, else summarize); image_path/image_path2.. ->
    image_analyzer (describe by default; OCR/detect when prompt asks). Never invent paths.
M2. doc_analyzer/tools/providers.py — real pypdf extract_text: PdfReader(path);
    _parse_pages("3"|"1-4"|None) -> 1-indexed inclusive range; join non-empty page texts;
    ExtractedText(pages=len(reader.pages)). Remove mock branch.
M3. doc_analyzer/config.py — drop extract_provider. M4. doc_analyzer/pyproject.toml — +pypdf>=5.0.0.
M5. web_agent/config.py — drop dead search_/weather_ fields.
M6. mcp/.env.example — drop DOC_ANALYZER_EXTRACT_PROVIDER block.

### Backend (6 files)
B1. _common/env/settings.py — OrchestratorMode = Literal["stdio","http"] (mock gone);
    + upload_dir: str = "./uploads" (GATEWAY_UPLOAD_DIR).
B2. services/orchestrator_client.py — delete MockOrchestratorClient + factory branch;
    factory raises ValueError on unknown mode; docstrings updated.
B3. services/chat_service.py — + ALLOWED_TYPES map {mime->kind: image|pdf},
    MAX_FILE_BYTES=15MB; `async save_uploads(files) -> dict[str,str]` (uuid4 filename with
    original suffix under settings.upload_dir; keys pdf_path, pdf_path2.., image_path..);
    GatewayError on bad type/size/read; `reply_with_files(prompt, files)` = save + reply.
B4. routers/chat.py — POST /api/chat/files: prompt: Annotated[str, Form()],
    files: list[UploadFile]; strip() -> empty prompt = fail envelope "prompt is required";
    delegates to service; same fail-soft pattern.
B5. pyproject.toml — + python-multipart>=0.0.9.
B6. backend/CLAUDE.md rule 6 — modes are stdio|http only, no mock stub (doc consistency).

### Compose / env (2 files)
C1. docker-compose.yml — volumes: uploads; mcp: mount uploads:/data/uploads, env
    GEMMA_API_KEY: "${GEMMA_API_KEY:?GEMMA_API_KEY is required}" (early fail), drop
    ORCHESTRATOR_LLM_PROVIDER; backend: mount uploads:/data/uploads, env
    GATEWAY_ORCHESTRATOR_MODE: "http" (fixed), GATEWAY_UPLOAD_DIR: /data/uploads.
C2. root .env.example — drop GATEWAY_ORCHESTRATOR_MODE + ORCHESTRATOR_LLM_PROVIDER mock
    lines; keep GEMMA_API_KEY (required note).

### Frontend (7 files)
F1. types/chat.d.ts — SendMessageRequest{prompt, files?: File[]}; ChatMessage +
    attachments?: string[].
F2. services/chatService.ts — files?.length ? FormData POST /api/chat/files : JSON
    /api/chat; same envelope handling.
F3. stores/chatStore.ts — send(prompt, files?) — text required (trim), attachments names
    recorded on the user message.
F4. ui-kit/MessageInput.tsx — hidden <input type=file multiple accept=".pdf,image/png,
    image/jpeg,image/webp,image/gif"> + attach button + removable file chips; submit
    requires non-empty text (button disabled + guard) regardless of files; emits
    onSend(text, files); clears both.
F5. ui-kit/MessageBubble.tsx — optional attachments chip row (presentational only).
F6. features/chat/ChatView.tsx — wire send(text, files); header copy loses "stubbed" text.
F7. __tests__/{chatService,chatStore,page}.test.* — update for new signatures + required
    prompt + multipart branch.

### Validation
py_compile + source asserts (A1, A4); stubbed runtime: pypdf pages parsing (A2), gateway
save_uploads/validation (A3); frontend: node_modules present -> `tsc --noEmit` + `jest`
offline (A5); compose file asserts (A6).
