# VALIDATION — 2026-07-13-scheduler-agent

## v1 — FAIL

Independent review (subagent) + spot checks against TASK.md R1-R10 / A1-A7.

PASS: R2/R8 (request unmodified; message always in envelope — tools/schedule.py,
scheduler_service._apply all branches). R3/R5 (time_local sole clock; astimezone UTC;
no server datetime.now in parse/schedule path). R4/R9 (clarify/reject early-return, no
DB/job). R6 (events columns exact — db/models.py). R7 (DB upsert before schedule_event;
job keyed by thread_id; jobstore separate; DB authoritative). Fail-soft envelope. Folder/
layering conformance to mcp/CLAUDE.md. A2 math verified 16:00-03:00 -> 19:00Z.

### Blocking issues
- id: I1  type: logic  severity: high  ref: mcp/Dockerfile:16-17
  note: Deployed mcp image installs only web_agent/doc_analyzer/image_analyzer/
  master_orchestrator; scheduler_agent is omitted. But master_orchestrator/config.py now
  spawns `python -m scheduler_agent.main` over stdio, so in the composed stack the module
  is absent -> ModuleNotFoundError on sub-agent load. R10 fleet-wiring incomplete for the
  deploy image; A1/A5 unattainable in the container. Fix = add ./scheduler_agent to the
  Dockerfile pip install (and update its header comment). No requirement/architecture
  change needed (R10 already mandates this; PLAN "wire into the fleet" covers it) -> logic
  fix by Executor.

Routing: type=logic -> Executor, exec_version bump.

## v2 — PASS

Re-check of I1 (exec_version=2): mcp/Dockerfile:17 now installs ./scheduler_agent, so the
orchestrator's registered `python -m scheduler_agent.main` stdio spawn resolves in the
composed image. Header comment updated. No new issues; v1 PASS findings (R2-R9, envelope,
DB-first ordering, time/UTC handling, R6 schema, folder/layering) unaffected by the
one-line Dockerfile change. open_issues empty.

Verdict: PASS. All requirements R1-R10 and acceptance A1-A7 met (A2/A5 runtime behaviour
validated by pure-logic checks + code review; live end-to-end with real Postgres/LLM not
executable in the offline sandbox but contracts and wiring conform).
