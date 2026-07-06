# EXEC — 2026-07-05-subagent-call-logging
## v1
subagent_client.py: call_subagent split into logging wrapper + _call_subagent (unchanged
body); one log line per call: "subagent <agent>.<tool> ok in Xs" (INFO) or
"... FAILED in Xs: <error>" (WARNING). 1 file.
