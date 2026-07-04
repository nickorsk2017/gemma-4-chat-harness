#!/usr/bin/env python3
"""Harness runner — deterministic task registry + dispatcher.

Commands:
  new <id> [--complexity LOW|MEDIUM|HIGH]  scaffold a task, make it active
  list                                     all tasks: stage/status/next_actor
  use <id>                                 switch the active task
  active                                   print active task id
  status [id]                              key STATE fields (active if omitted)
  next [id]                                dispatch descriptor for next_actor

The runner never decides content — it only resolves routing from STATE.yaml,
the single source of truth. next_actor drives everything.
"""
import argparse, os, sys, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(ROOT, "tasks")
ACTIVE = os.path.join(TASKS, "ACTIVE")

ROLE_IO = {
    "Planner":   (["TASK.md","STATE.yaml"], ["PLAN.md","STATE.yaml"]),
    "Executor":  (["TASK.md","PLAN.md","STATE.yaml"], ["EXEC.md","STATE.yaml"]),
    "Validator": (["TASK.md","PLAN.md","EXEC.md","STATE.yaml"], ["VALIDATION.md","STATE.yaml"]),
    "Engineer":  (["<all>"], ["TASK.md","STATE.yaml"]),
}
FIRST_ACTOR = {"LOW": "Executor", "MEDIUM": "Planner", "HIGH": "Planner"}

def die(m): print(f"error: {m}", file=sys.stderr); sys.exit(1)
def tdir(tid): return os.path.join(TASKS, tid)
def spath(tid): return os.path.join(tdir(tid), "STATE.yaml")

def field(text, key):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(key + ":"):
            return s.split(":",1)[1].split("#")[0].strip()
    return None

def read_state(tid):
    p = spath(tid)
    if not os.path.isfile(p): die(f"no such task '{tid}'")
    return open(p, encoding="utf-8").read()

def all_tasks():
    if not os.path.isdir(TASKS): return []
    return sorted(d for d in os.listdir(TASKS)
                  if os.path.isfile(spath(d)))

def get_active():
    if os.path.isfile(ACTIVE):
        return open(ACTIVE).read().strip() or None
    return None

def set_active(tid):
    open(ACTIVE, "w").write(tid + "\n")

def resolve(tid):
    return tid or get_active() or die("no active task; use `runner.py use <id>`")

def log(tid, line):
    p = os.path.join(tdir(tid), "LOG.md")
    ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    with open(p, "a", encoding="utf-8") as f:
        f.write(f"- {ts} {line}\n")

# ---- commands ----
def cmd_new(a):
    tid = a.id
    d = tdir(tid)
    if os.path.exists(d): die(f"task '{tid}' already exists")
    os.makedirs(d)
    cx = a.complexity
    actor = FIRST_ACTOR[cx]
    open(os.path.join(d,"TASK.md"),"w").write(
        f"# TASK — {tid}\nowner: Engineer\nimmutable: true\n\n## Requirements\n- R1: \n\n## Acceptance\n- A1: \n\n## Constraints\n- \n")
    for f in ("PLAN.md","EXEC.md","VALIDATION.md"):
        open(os.path.join(d,f),"w").write(f"# {f.split('.')[0]} — {tid}\n")
    open(os.path.join(d,"STATE.yaml"),"w").write(
        f"task_id: {tid}\nstage: INIT\nstatus: PENDING\niteration: 0\n"
        f"complexity: {cx}\nnext_actor: {actor}\nplan_version: 0\n"
        f"exec_version: 0\nvalidation_version: 0\nopen_issues: []\nlast_error: null\n")
    open(os.path.join(d,"LOG.md"),"w").write(f"# LOG — {tid}\n")
    log(tid, f"Engineer INIT task created, complexity={cx}, next_actor={actor}")
    set_active(tid)
    print(f"created '{tid}' [{cx}] -> INIT, next_actor={actor} (now active)")

def cmd_list(a):
    act = get_active()
    ts = all_tasks()
    if not ts: print("(no tasks)"); return
    print(f"{'':2}{'TASK':22}{'STAGE':11}{'STATUS':9}{'NEXT_ACTOR'}")
    for t in ts:
        s = read_state(t)
        mark = "*" if t == act else " "
        print(f"{mark:2}{t:22}{field(s,'stage') or '?':11}"
              f"{field(s,'status') or '?':9}{field(s,'next_actor') or '?'}")

def cmd_use(a):
    if not os.path.isfile(spath(a.id)): die(f"no such task '{a.id}'")
    set_active(a.id); print(f"active task -> {a.id}")

def cmd_active(a):
    print(get_active() or "(none)")

def cmd_status(a):
    tid = resolve(a.id); s = read_state(tid)
    for k in ("task_id","stage","status","iteration","complexity",
              "next_actor","open_issues","last_error"):
        print(f"{k:14}{field(s,k)}")

def cmd_next(a):
    tid = resolve(a.id); s = read_state(tid)
    stage, actor = field(s,"stage"), field(s,"next_actor")
    if stage == "DONE" or actor in (None,"","none"):
        print(f"[{tid}] {stage}: nothing to dispatch."); return
    reads, writes = ROLE_IO.get(actor, (["?"],["?"]))
    oi = field(s,"open_issues")
    print(f"DISPATCH  task={tid}  stage={stage}  actor={actor}")
    print(f"  skill : skills/{actor}/SKILLS.md")
    print(f"  reads : {', '.join(reads)}")
    print(f"  writes: {', '.join(writes)}")
    if oi and oi != "[]":
        print(f"  open_issues: {oi}")
    if actor == "Engineer" and stage == "PLANNED":
        print("  action: HIGH-complexity plan awaiting approval "
              "(set stage=APPROVED) or requirement rework.")


def cmd_done(a):
    tid = resolve(a.id); s = read_state(tid)
    stage, status = field(s,"stage"), field(s,"status")
    oi = field(s,"open_issues")
    clean = stage == "DONE" and status == "PASS" and oi in (None,"[]","")
    if not clean and not a.force:
        die(f"task '{tid}' not finished: stage={stage} status={status} "
            f"open_issues={oi}. Close it via the pipeline, or use --force.")
    if not clean:
        print(f"warning: forcing close of unfinished task "
              f"(stage={stage} status={status})")
    if get_active() == tid or a.id is None:
        set_active("")  # ACTIVE -> none
    log(tid, f"Engineer CLOSED task done={clean} (active cleared)")
    print(f"\u2714 task '{tid}' closed. active task -> none.")
    print("  all state is in artifacts \u2014 the Claude window is safe to clear "
          "now (/clear or start a new session).")

def cmd_install_hooks(a):
    repo = os.path.dirname(ROOT)  # .claude lives at <repo>/.claude
    rc = os.system(f'git -C "{repo}" config core.hooksPath .claude/githooks')
    if rc == 0:
        print("core.hooksPath -> .claude/githooks (pre-commit gate active)")
    else:
        die("git config failed (is this a git repo?)")

def main():
    p = argparse.ArgumentParser(prog="runner.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("id")
    n.add_argument("--complexity", choices=["LOW","MEDIUM","HIGH"], default="MEDIUM")
    n.set_defaults(fn=cmd_new)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    u = sub.add_parser("use"); u.add_argument("id"); u.set_defaults(fn=cmd_use)
    sub.add_parser("active").set_defaults(fn=cmd_active)
    st = sub.add_parser("status"); st.add_argument("id", nargs="?"); st.set_defaults(fn=cmd_status)
    nx = sub.add_parser("next"); nx.add_argument("id", nargs="?"); nx.set_defaults(fn=cmd_next)
    d = sub.add_parser("done"); d.add_argument("id", nargs="?")
    d.add_argument("--force", action="store_true"); d.set_defaults(fn=cmd_done)
    sub.add_parser("install-hooks").set_defaults(fn=cmd_install_hooks)
    a = p.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
