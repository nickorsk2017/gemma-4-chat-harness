# EXEC — thin-gateway-proxy
exec_version: 1

## v1 — implementation (per PLAN v1)

### Gateway = pure proxy
- services/orchestrator_client.py DELETED; replaced by services/agent_client.py:
  one class McpAgentClient (target = URL if mode==http else {command,args}, fed to
  fastmcp Client), Protocol AgentClient, AgentOutcome{ok,data:dict,error}. Success
  passes the agent's OrchestrationResult dict through verbatim; _to_outcome maps the
  AgentResponse envelope; delete proxied. build_agent_client factory.
- services/chat_service.py: thin proxy. reply(prompt,file,thread_id)->AgentOutcome;
  reply_with_files base64-encodes the single upload (_encode) with NO validation;
  delete_thread proxied. No thread_id generation, no GatewayValidationError.
- routers/chat.py: _reply maps AgentOutcome -> ApiResponse[AgentData] (ok->200,
  agent error->502). Uses build_agent_client. Removed 400 validation branch.
- schemas/chat.py: added AgentData(extra=allow){answer, thread_id}; ChatRequest keeps
  {prompt,file?,thread_id?}; removed ChatReply. Kept FilePayload, DeleteThreadReply.
- schemas/__init__.py + services/__init__.py: re-exports updated to new symbols.

### Agent owns logic
- schemas/http.py: OrchestrationResult += thread_id (required).
- config.py: + max_file_bytes (15 MiB).
- prompts/orchestrate.py: English base ORCHESTRATOR_SYSTEM + 3 directives
  PROCESS_PDF_SYSTEM / PROCESS_IMAGE_SYSTEM / GET_FROM_INTERNET_SYSTEM. Removed file_hint.
- prompts/generator.py (NEW): PromptGenerator(request).system_messages() -> base + one
  directive by payload (PDF/Image/no-file->internet), via FileKind.
- tools/orchestrator.py: _validate(request) (unsupported kind / oversize; empty prompt via
  schema); thread_id = request.thread_id or uuid4().hex, returned in result; system prompts
  from PromptGenerator; kept tool loop, raw-file injection, thread memory.

### Frontend
- services/chatService.ts: reads envelope.data.answer (was reply) + data.thread_id;
  local ChatReply interface field renamed reply->answer.
- __tests__/chatService.test.ts: mocks updated to {data:{answer,...}} incl. thread echo.

### Backend tests
- test_uploads.py: proxy base64s + forwards; unsupported type is forwarded (not rejected);
  empty list -> None. Uses a capture fake client + AgentOutcome.
- test_chat_thread.py: gateway forwards thread_id as-is (incl None) and echoes agent's;
  delete proxied; failure surfaced. FakeClient.send/delete return AgentOutcome.
