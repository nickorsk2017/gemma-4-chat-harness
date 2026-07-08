# TASK — 2026-07-07-file-passthrough-rearch
owner: Engineer
immutable: true

## Requirements
- R1: Gateway decides nothing — it only forwards the request to master_orchestrator.
  Remove all orchestration/pre-processing from the gateway (PDF text extraction,
  image-to-disk saving, upload_dir usage). orchestrator_client.py becomes a thin
  passthrough of {prompt, file?, thread_id?}.
- R2: Orchestration logic lives in master_orchestrator's Gemma tool-calling loop
  (agent_core LLM). It receives the raw payload {prompt: string, file?: File}.
- R3: The LLM chooses which tool to call via prompts. Files are NOT processed by the
  orchestrator — they pass through unchanged to the chosen sub-agent.
- R4: The File contract is base64-inline: {filename, content_type, content_b64},
  shared by orchestrator and sub-agents (agent_core) and mirrored in the gateway.
- R5: When a file is present, a system prompt announces its type (Document or Image)
  so the LLM routes to the correct sub-agent tool.
- R6: Use LangChain to the maximum extent possible.
- R7: doc_analyzer and image_analyzer each expose ONE tool taking {prompt, file}.
- R8: doc_analyzer decodes the PDF via PyPDF -> text, then passes text+prompt to Gemma.
- R9: image_analyzer passes the image + prompt to Gemma (multimodal).
- R10: web_agent receives {prompt} and calls its Tavily provider
  (mcp/web_agent/providers/tavily.py) for live internet data.
- R11: Conversation memory (thread_id, history, delete_thread) is preserved.

## Acceptance
- A1: Gateway no longer imports pypdf, writes to upload_dir, or builds document_text/
  image_path context; /api/chat/files base64-encodes the upload and forwards it.
- A2: OrchestrateRequest == {prompt, file?: FilePayload, thread_id?} (no context).
- A3: Orchestrator injects the raw file into doc/image tool calls at dispatch; the model
  never carries file bytes; a Document/Image system hint is added when a file is present.
- A4: doc_analyzer exposes analyze_document({prompt, file}); image_analyzer exposes
  analyze_image({prompt, file}); web_agent search takes {prompt}.
- A5: All touched Python compiles; gateway unit tests updated to the new contract pass.

## Constraints
- Obey subsystem CLAUDE.md rules (contracts-first, thin tools/routers, prompts are data,
  config not constants, fail-soft envelopes). Precedence: .claude harness > root > subsystem.
- Keep the app "always real" (no mock LLM path); GEMMA_API_KEY/TAVILY_API_KEY still required.
