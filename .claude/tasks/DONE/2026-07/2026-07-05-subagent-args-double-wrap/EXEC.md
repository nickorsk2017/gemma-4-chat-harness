# EXEC — 2026-07-05-subagent-args-double-wrap
## v1
subagent_client.py: new `_shape_args(schema, arguments)` — pass-through when already
{"request": {...}} and schema expects `request`; wrap flat args; unwrap when schema is
flattened; non-dict "request" values are not treated as wrappers. Call site uses it. 1 file.
