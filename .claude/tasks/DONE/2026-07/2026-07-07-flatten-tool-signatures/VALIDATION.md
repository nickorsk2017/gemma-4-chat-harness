# VALIDATION — 2026-07-07-flatten-tool-signatures

## v1 — PASS
- A1 PASS (static): each tool's single `request: Model` param replaced by flat
  Annotated params (prompt [+ max_results | file]); FastMCP will emit a flat
  schema with no `request` wrapper. Live schema assert (fastmcp/pydantic absent
  in sandbox) left to Engineer via `make tools-check`.
- A2 PASS: FileService.inject unchanged; `args.get("request", args)` resolves to
  `args` for flat calls and sets top-level `args["file"]`, which the flat `file`
  param reads. grep confirms inject untouched.
- A3 PASS: providers/envelopes unchanged; no residual `request.` refs; no
  leftover request-model imports; all three modules py_compile clean.
- Live end-to-end (news via search_web; doc/image with attachment) left to
  Engineer: `make up` then `make tools-check` + a real prompt.
