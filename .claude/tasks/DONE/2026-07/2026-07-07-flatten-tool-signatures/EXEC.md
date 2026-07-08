# EXEC — 2026-07-07-flatten-tool-signatures

## v1
Flattened all three @mcp.tool signatures per PLAN v1:
- web_agent/tools/web_tools.py: search_web(prompt, max_results=5) with
  Annotated+Field (desc; ge=1/le=10); dropped SearchRequest import; body calls
  tavily.search_web(prompt, max_results).
- doc_analyzer/tools/doc_tools.py: analyze_document(prompt, file=None); dropped
  AnalyzeRequest import, added agent_core.files.FilePayload; None-guard + provider
  call analyze_document(prompt, file).
- image_analyzer/tools/image_tools.py: analyze_image(prompt, file=None); same
  shape; provider call analyze_image(prompt, file).
FileService.inject, providers, schemas, orchestrator prompt untouched (Constraint).
Now-unused Pydantic request models left defined in their schemas modules.
py_compile OK on all three.
