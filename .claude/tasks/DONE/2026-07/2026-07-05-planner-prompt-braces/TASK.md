# TASK — 2026-07-05-planner-prompt-braces
owner: Engineer
immutable: true

## Requirements
- R1: /api/chat/files fails with "Invalid format specifier in f-string template. Nested
  replacement fields are not allowed." — the planner system prompt contains literal JSON
  braces that ChatPromptTemplate parses as template fields. Escape every literal { } in
  PLANNER_SYSTEM (doubling), keeping {prompt}/{context}/{results} variables only in the
  human prompts.

## Acceptance
- A1: string.Formatter().parse over PLANNER_SYSTEM yields no replacement fields;
  PLANNER_HUMAN yields exactly {prompt, context}; SYNTHESIS_HUMAN exactly {prompt, results};
  SYNTHESIS_SYSTEM none. (This mirrors ChatPromptTemplate's f-string parsing.)
- A2: rendered system prompt still shows single braces (catalog readable by the LLM).
