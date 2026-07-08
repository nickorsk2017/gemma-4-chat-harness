# TASK — thin-gateway-proxy
owner: Engineer
immutable: true

## Requirements
- R1: The gateway is a PURE PROXY between the client (frontend) and the agent
  (master_orchestrator). It contains NO orchestration logic. It only bridges
  HTTP<->MCP: accept the request, (for uploads) base64-encode the file as transport,
  forward {prompt, file?, thread_id?} to the `orchestrate` MCP tool, and return the
  agent's response wrapped in the REST ApiResponse envelope.
- R2: Collapse the two near-identical MCP client classes (Stdio/Http) into ONE client;
  fastmcp Client already accepts either a stdio spec or a URL. Keep the Protocol (tests
  stub it; backend rule 6). Rename the module to reflect it is the agent transport.
- R3: Move thread_id GENERATION into the agent. The gateway no longer generates it; the
  agent generates a thread_id when the request omits one, uses it for memory, and returns
  it so the client can continue the conversation.
- R4: Move INPUT VALIDATION into the agent (empty prompt; unsupported file type; file too
  large). The gateway does not validate these.
- R5: Conversation memory (Postgres thread store) stays in master_orchestrator (already there).
- R6: The agent inserts the payload into a PromptGenerator class that builds the system
  prompt(s) for the turn:
    * file present & PDF  -> system prompt: process the PDF (route to analyze_document).
    * file present & Image -> system prompt: process the image (route to analyze_image).
    * no file -> add a system prompt: get data from the internet (route to search_web).
  All prompts are in ENGLISH.
- R7: Frontend adapts to the agent's response shape (answer + thread_id) so chat keeps working.

## Acceptance
- A1: gateway/services has ONE agent client class + a thin proxy service; no thread_id
  generation and no prompt/file validation remain in the gateway.
- A2: OrchestrationResult includes thread_id; orchestrator generates it when absent.
- A3: A PromptGenerator class in master_orchestrator/prompts builds English system prompts
  by payload kind (PDF / Image / no-file -> internet).
- A4: master_orchestrator validates empty prompt + unsupported/oversized file and returns a
  fail envelope.
- A5: frontend chatService + all backend/frontend tests updated and consistent; touched
  Python compiles.

## Constraints
- Precedence: .claude harness > root > subsystem CLAUDE.md. Keep ApiResponse envelope
  (backend rule 3), thin routers (rule 2), fail-soft (mcp rule 7), prompts-as-data (mcp
  rule 4), config-not-constants (rule 5). Always real (no mock LLM path).
