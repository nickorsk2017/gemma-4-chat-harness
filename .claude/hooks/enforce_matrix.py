#!/usr/bin/env python3
"""PreToolUse guard for the artifact harness.

1) Write matrix: an actor may only write artifacts in its own column.
2) State machine: a STATE.yaml write may only advance `stage` along a legal edge.

Current actor = STATE.yaml.next_actor in the artifact's task dir.
Non-artifact files (real source code) pass through untouched.
Exit 2 = block (stderr shown to the model); exit 0 = allow.
"""
import json, os, sys

GOVERNED = {"TASK.md", "PLAN.md", "EXEC.md", "VALIDATION.md", "STATE.yaml"}
MATRIX = {
    "Engineer":  {"TASK.md", "STATE.yaml"},
    "Planner":   {"PLAN.md", "STATE.yaml"},
    "Executor":  {"EXEC.md", "STATE.yaml"},
    "Validator": {"VALIDATION.md", "STATE.yaml"},
}
# Legal stage edges (from -> allowed set). from==to is always allowed
# (version bumps / open_issues edits without a stage change).
TRANSITIONS = {
    "INIT":      {"PLANNED", "EXECUTED"},
    "PLANNED":   {"APPROVED", "EXECUTED"},
    "APPROVED":  {"EXECUTED"},
    "EXECUTED":  {"VALIDATED"},
    "VALIDATED": {"DONE", "PLANNED", "EXECUTED", "INIT", "ESCALATED"},
    "ESCALATED": {"INIT", "PLANNED", "APPROVED"},
    "DONE":      set(),  # terminal
}

def deny(msg):
    print(f"[matrix] BLOCKED: {msg}", file=sys.stderr)
    sys.exit(2)

def field(text, key):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(key + ":"):
            return s.split(":", 1)[1].split("#")[0].strip()
    return None

def resulting_content(ti, current):
    """Reconstruct the file text this Write/Edit would produce."""
    if "content" in ti and ti.get("content") is not None:      # Write
        return ti["content"]
    if "new_string" in ti:                                     # Edit
        if current is None:
            return None
        old, new = ti.get("old_string", ""), ti.get("new_string", "")
        if ti.get("replace_all"):
            return current.replace(old, new)
        return current.replace(old, new, 1)
    return None

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    fp = ti.get("file_path") or ti.get("path")
    if not fp:
        sys.exit(0)

    base = os.path.basename(fp)
    if base not in GOVERNED:
        sys.exit(0)  # source code / other files: not governed

    task_dir = os.path.dirname(os.path.abspath(fp))
    state_path = os.path.join(task_dir, "STATE.yaml")
    if not os.path.isfile(state_path):
        sys.exit(0)  # artifact outside a task dir

    state_text = open(state_path, encoding="utf-8").read()
    actor = field(state_text, "next_actor")

    # (1) write-matrix check
    if actor not in (None, "", "none"):
        if actor not in MATRIX:
            deny(f"unknown next_actor '{actor}' in {state_path}")
        if base not in MATRIX[actor]:
            allowed = ", ".join(sorted(MATRIX[actor]))
            deny(f"{actor} may not write {base}. Allowed: {allowed}.")

    # (2) state-machine check (only for STATE.yaml writes on an existing file)
    if base == "STATE.yaml":
        cur = state_text if os.path.abspath(fp) == state_path else \
              (open(fp, encoding="utf-8").read() if os.path.isfile(fp) else None)
        new_text = resulting_content(ti, cur)
        if new_text is None or cur is None:
            sys.exit(0)  # creation or unreconstructable -> don't block
        old_stage, new_stage = field(cur, "stage"), field(new_text, "stage")
        if old_stage and new_stage and old_stage != new_stage:
            if new_stage not in TRANSITIONS.get(old_stage, set()):
                legal = ", ".join(sorted(TRANSITIONS.get(old_stage, set()))) or "(none: terminal)"
                deny(f"illegal transition {old_stage} -> {new_stage}. "
                     f"Legal from {old_stage}: {legal}.")

    sys.exit(0)

if __name__ == "__main__":
    main()
