# VALIDATION — 2026-07-05-llm-timeouts
## v1 — PASS
A1: source checks — gateway 180 > subagent 120 (nested budgets), compose + example env in
sync; both files compile. Root cause: 30s gateway cap < real chain (planner + doc gemma
call + synthesis), per user's timing (~40s request hit the cap).
