#!/usr/bin/env python3
"""Server-side harness gate — scans ALL tasks, fails the build on broken state.

Unlike the local pre-commit hook (which guards the ACTIVE task), CI enforces
repo-wide invariants that must never land on a shared branch:
  - no task in stage ESCALATED
  - no task with non-empty open_issues
  - every STATE.yaml has a known stage and an internally consistent status
DONE tasks are fine — that is the intended committed end state.
Exit 1 on any violation. Run: python3 .claude/scripts/ci_check.py
"""
import os, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # .claude/ (scripts/ lives under it)
TASKS = os.path.join(ROOT, "tasks")
STAGES = {"INIT","PLANNED","APPROVED","EXECUTED","VALIDATED","DONE","ESCALATED"}
STATUSES = {"PENDING","PASS","FAIL"}

def field(text, key):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(key + ":"):
            return s.split(":",1)[1].split("#")[0].strip()
    return None

def main():
    viol = []
    # open tasks only: tasks/<YYYY-MM>/<id>/STATE.yaml (archive DONE/ is clean by construction)
    states = sorted(glob.glob(os.path.join(TASKS, "*", "*", "STATE.yaml")))
    for sp in states:
        tid = os.path.basename(os.path.dirname(sp))
        s = open(sp, encoding="utf-8").read()
        stage, status, oi = field(s,"stage"), field(s,"status"), field(s,"open_issues")
        if stage not in STAGES:
            viol.append(f"{tid}: unknown stage '{stage}'")
        if status not in STATUSES:
            viol.append(f"{tid}: unknown status '{status}'")
        if stage == "ESCALATED":
            viol.append(f"{tid}: ESCALATED — unresolved, must not be on the branch")
        if oi not in (None, "[]", ""):
            viol.append(f"{tid}: unresolved open_issues {oi}")
        if stage == "DONE" and status != "PASS":
            viol.append(f"{tid}: DONE but status={status} (must be PASS)")
    print(f"harness gate: scanned {len(states)} task(s)")
    if viol:
        print("VIOLATIONS:", file=sys.stderr)
        for v in viol:
            print(f"  ✖ {v}", file=sys.stderr)
        sys.exit(1)
    print("✔ all tasks clean")
    sys.exit(0)

if __name__ == "__main__":
    main()
