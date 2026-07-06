# VALIDATION — 2026-07-05-planner-prompt-braces
## v1 — PASS
A1: string.Formatter parse — PLANNER_SYSTEM has zero replacement fields; PLANNER_HUMAN =
{prompt, context}; SYNTHESIS_HUMAN = {prompt, results}; SYNTHESIS_SYSTEM none.
A2: .format() renders the catalog with single braces, no residual doubling.
(Formatter mirrors ChatPromptTemplate's f-string parser — the original exception
"Nested replacement fields are not allowed" is no longer reachable.)
