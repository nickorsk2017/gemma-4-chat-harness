# VALIDATION — 2026-07-05-single-file-limit

## v1 — PASS
- A1 PASS: MessageInput has no `multiple`; new pick replaces current file (source check).
- A2 PASS: stub runtime — gateway save_uploads raises "only one file can be attached per
  message" on 2 files, accepts 1; client service guard "Only one file" present and covered
  by a new jest case (host-run, see below).
- A3 PASS: tsc --noEmit clean; chat_service.py compiles.
Residual (carried over): jest must run on the host (sandbox lacks the SWC binary).
