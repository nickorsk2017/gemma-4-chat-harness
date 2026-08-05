# PLAN — thin-gateway-proxy
plan_version: 1

## v1

### Shape after change
Frontend -> gateway (proxy) -> master_orchestrator (all logic) -> sub-agents.
Gateway does zero decisions: HTTP<->MCP bridge + base64 of uploads + ApiResponse wrap.
Agent owns: thread_id generation, validation, PromptGenerator routing, memory, merge.

### File-by-file

# Gateway
1. services/orchestrator_client.py -> RENAME to services/agent_client.py.
   - One class `McpAgentClient` (was Stdio+Http). Target = URL when mode==http else
     {command,args}; both fed straight to fastmcp Client (already `spec: Any`).
   - Protocol renamed `AgentClient`. Methods: send(prompt, file, thread_id) -> AgentOutcome;
     delete_thread(thread_id) -> AgentOutcome.
   - AgentOutcome{ok, data: dict, error}. On success `data` = agent OrchestrationResult dict
     (answer, thread_id, results) passed through verbatim. No answer/subtasks re-derivation.
   - Keep _extract + envelope->outcome mapping (ok/error) only; that is transport, not logic.
2. services/chat_service.py -> thin proxy service.
   - reply(prompt, file, thread_id): call client.send; return AgentOutcome. NO thread_id gen.
   - reply_with_files(prompt, files, thread_id): base64 the single upload into FilePayload
     (transport only; NO type/size/prompt validation) then call reply.
   - delete_thread(thread_id): proxy. (Blank-id guard is transport-level; keep minimal.)
3. routers/chat.py: map AgentOutcome -> ApiResponse. ok -> Success(200, data). error -> Failed(502).
   Remove GatewayValidationError 400 branch (validation now agent-side). Response model
   ApiResponse[dict] (passthrough of agent data) — or ApiResponse[AgentData] typed model.
   Decision: introduce gateway schema `AgentData{answer, thread_id, results?}` for typing.
4. schemas/chat.py: keep FilePayload; ChatRequest{prompt, file?, thread_id?}. Add AgentData
   response model. Drop ChatReply/DeleteThreadReply if unused (keep DeleteThreadReply thin).
5. _common/env/settings.py: unchanged (orchestrator_* transport settings stay; they name the
   agent, not gateway logic).

# Agent (master_orchestrator)
6. schemas/http.py: OrchestrationResult += thread_id: str.
7. config.py: add max_file_bytes (15 MiB default). allowed types come from agent_core.files.
8. prompts/orchestrate.py: base ORCHESTRATOR_SYSTEM (tools) + English directives:
   PROCESS_PDF_SYSTEM, PROCESS_IMAGE_SYSTEM, GET_FROM_INTERNET_SYSTEM.
9. prompts/generator.py (NEW): class PromptGenerator(request). Method system_messages() ->
   list[str]: base + (PDF|Image directive when file present) or (internet directive when no
   file). classify via file.kind (agent_core.files).
10. tools/orchestrator.py:
    - thread_id = request.thread_id or uuid4().hex; use it; put into OrchestrationResult.
    - validate: if file: file.kind is None -> raise ValueError(unsupported type);
      len(file.decode_bytes()) > settings.max_file_bytes -> raise ValueError(too large).
      (empty prompt already enforced by OrchestrateRequest.min_length=1.)
    - build system messages from PromptGenerator(request).system_messages().
    - keep tool loop + raw-file injection + thread memory (messages).

# Frontend
11. services/chatService.ts: read envelope.data.answer (was .reply) + data.thread_id.
    Keep client-side UX guards (empty prompt / >1 file). Update the "no reply" check to answer.
12. __tests__/chatService.test.ts: mocks {data:{answer:...}} instead of {data:{reply:...}}.

# Tests (backend)
13. tests/test_uploads.py: process_uploads only base64s (no unsupported-type rejection here).
14. tests/test_chat_thread.py: gateway forwards thread_id as-is (incl. None); echoes agent's
    returned thread_id; delete proxied. FakeClient.send(prompt, file, thread_id)->AgentOutcome
    carrying data{answer, thread_id}.

### Notes / risks
- R6 "no file -> get from internet" will bias every text-only turn toward web search
  (incl. small talk). Implemented per instruction; phrased as an instruction to use search_web.
- Renames touch imports (router, tests) — update together.
- HTTP status for agent-side validation failures = 502 Failed (proxy can't distinguish client
  vs server from the envelope); acceptable under "validation in agent".
