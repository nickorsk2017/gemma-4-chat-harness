# PLAN — 2026-07-07-flatten-tool-signatures

## v1

### Problem
Each @mcp.tool takes ONE param `request: <Model>`, so FastMCP emits a schema
`{"required":["request"],"properties":{"request":{...}}}`. The model must produce
`{"request":{"prompt":...}}` while the system prompt tells it to pass `prompt`.
Mismatch + opaque wrapper name = weak callers (Gemma) don't emit a valid call.

### Approach
Replace the single Pydantic-model param with explicit flat params, keeping
descriptions/bounds via `Annotated[..., Field(...)]`. FastMCP then generates a
flat schema whose top-level keys match the prompt. Providers and envelopes are
untouched; only the tool function boundary changes.

### Change set (3 files, tool modules only)

1. web_agent/tools/web_tools.py
   - Drop `from web_agent.schemas.http import SearchRequest`.
   - Add `from typing import Annotated` and `from pydantic import Field`.
   - Signature:
       async def search_web(
           prompt: Annotated[str, Field(description="What to search the live web for.")],
           max_results: Annotated[int, Field(ge=1, le=10, description="Max results (1-10).")] = 5,
       ) -> AgentResponse[SearchResult]:
   - Body: `result = await tavily.search_web(prompt, max_results)`.
   - Keep docstring (tool description) and @traceable decorators as-is.

2. doc_analyzer/tools/doc_tools.py
   - Drop `from doc_analyzer.schemas.http import AnalyzeRequest`;
     add `from agent_core.files import FilePayload`, `from typing import Annotated`,
     `from pydantic import Field`.
   - Signature:
       async def analyze_document(
           prompt: Annotated[str, Field(min_length=1, description="Instruction about the document.")],
           file: FilePayload | None = None,
       ) -> AgentResponse[DocAnalysis]:
   - Body: guard `if file is None: return AgentResponse.fail(AGENT, "no document file was provided")`,
     then `result = await providers.analyze_document(prompt, file)`.

3. image_analyzer/tools/image_tools.py
   - Same shape as (2) with AnalyzeImageRequest -> flat `prompt`, `file`;
     provider call `await providers.analyze_image(prompt, file)`; fail msg
     "no image file was provided".

### Why FileService.inject needs NO change
`inject()` does `payload = args.get("request", args)` then `payload["file"] = ...`.
With a flat schema there is no `"request"` key, so `payload` IS `args` and the
file lands at top-level `args["file"]` — exactly where the flat `file` param
reads it. Confirmed flatten-tolerant; leave it untouched (Constraint).

### Unused artifacts
The Pydantic request models (SearchRequest/AnalyzeRequest/AnalyzeImageRequest)
become unused but are LEFT DEFINED in their schemas modules (harmless, mirrors
the existing legacy NewsRequest/WeatherRequest/FetchRequest). Only the now-unused
imports in the tool files are removed, so ruff stays clean.

### Risk / validation
- Sandbox lacks fastmcp+pydantic, so live schema generation can't be asserted
  here; Validator does py_compile on all three + static review. Live schema
  check (`make tools-check` shows flat schema, no `request` wrapper) and a real
  news/doc/image run are left to the Engineer.
- No new deps; provider/envelope contracts unchanged -> end-to-end behaviour
  preserved.
