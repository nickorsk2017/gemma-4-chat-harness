# TASK — 2026-07-07-orchestrator-tools-nonempty
owner: Engineer
immutable: true

## Requirements
- R1: Script `mcp/scripts/tools_check.py` that reproduces the orchestrator's
  tool-binding step (`SubagentToolset.load()`) and verifies the bound tool list
  is NOT empty — the exact `loaded.tools` passed to `get_llm().bind_tools(...)`.
- R2: Print each discovered tool's name and its args schema; explicitly report
  whether `search_web` (web_agent) is present, since that is the tool the news
  path depends on.
- R3: Exit 0 only when the list is non-empty AND `search_web` is present;
  exit 1 otherwise (empty list, missing search_web, or load error), with a
  readable stderr message. No LLM call — this isolates discovery/binding from
  the model's tool-calling behaviour.

## Acceptance
- A1: Running the script prints the tool names + count and a clear PASS/FAIL line.
- A2: Empty list or absent `search_web` or a load exception -> stderr + exit 1.

## Constraints
- Single file, no new dependencies (reuse master_orchestrator + langchain deps).
