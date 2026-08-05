# EXEC — 2026-08-02-dev-stop-port-sweep

## v1

Single file touched: root `Makefile`. LOW task — no plan artifact; implemented directly
from TASK.md R1-R6.

### Changed
| Location | Change | Reqs |
|---|---|---|
| `define dev_kill` | takes a 2nd arg (port expr); sources `$(LOAD_ENV)` itself so each service shell sees `.env`; after the pid-file kill it sweeps the port: TERM -> poll 5x1s -> KILL -> re-check | R2, R3, R5 |
| `define dev_kill` | `command -v lsof` guard: prints "lsof not found — port N not swept" and continues | R4 |
| `dev-stop` recipe | `$(foreach s,$(DEV_SERVICES),...)` replaced by three explicit `$(call dev_kill,<svc>,<port expr>)` lines, each `@`-prefixed, so every service passes its own port | R1, R3 |

### Notes
- Port exprs are `$${MCP_PORT:-$(DEV_MCP_PORT)}` etc. — the same precedence `dev` and
  `dev-ps` use, so an override applies to start, status and stop consistently (R3).
- `$(LOAD_ENV)` moved INSIDE the define rather than onto the `dev-stop` recipe: the define's
  body is one continued logical line per service, i.e. three separate shells — a single
  recipe-level `$(LOAD_ENV)` would only have covered the first.
- The pid-file branch keeps its behaviour; its "not running" messages now distinguish a
  stale pid file from a missing one (R5). `rm -f` of the pid file still precedes the sweep.
- `dev-restart` inherits the fix with no edit (R6).

### Deviation
None from TASK.md. One in-flight correction: the first cut piped `$$holders` through `tr`
and lost the space before the em dash ("held by 8— sending TERM"); replaced with
`$$(echo $$holders)`, which collapses the newlines anyway.
