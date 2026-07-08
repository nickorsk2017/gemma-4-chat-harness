#!/usr/bin/env python3
"""tools_check.py — verify the orchestrator binds a NON-EMPTY tool set.

Reproduces the exact discovery/binding step the orchestrator runs at the top of
its loop::

    loaded = await SubagentToolset.load()
    model  = get_llm().bind_tools(loaded.tools)   # <- loaded.tools must be non-empty

No LLM is called: this isolates "were any tools discovered and bound?" from the
separate question of whether the model actually emits tool calls. Each configured
sub-agent is spawned over MCP stdio and queried for its tools; the script prints
every tool's name + args schema, and fails if the list is empty or if
``search_web`` (the web_agent tool the news path needs) is absent.

Exit 0  -> tools non-empty AND search_web present.
Exit 1  -> empty list, search_web missing, or a load error.

Run from the ``mcp/`` directory (or anywhere the agent packages are installed):
    python3 scripts/tools_check.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Make the agent packages importable and inheritable by spawned sub-agents even
# when this script is run without an editable install: prepend mcp/ to sys.path
# AND to PYTHONPATH (the stdio sub-agent processes inherit our environment).
_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))
os.environ["PYTHONPATH"] = os.pathsep.join(
    p for p in (str(_MCP_DIR), os.environ.get("PYTHONPATH", "")) if p
)

REQUIRED_TOOL = "search_web"  # web_agent's tool; the news path depends on it


def _schema_of(tool) -> object:
    """Best-effort JSON schema for a LangChain tool's args (version-tolerant)."""
    schema = getattr(tool, "args_schema", None)
    if schema is None:
        return None
    for attr in ("model_json_schema", "schema"):  # pydantic v2, then v1
        fn = getattr(schema, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:  # noqa: BLE001 - schema is diagnostic only
                return str(schema)
    return str(schema)


async def _main() -> int:
    # Imported here so a missing/broken agent package surfaces as a clean
    # exit-1 error instead of an uncaught traceback.
    try:
        from master_orchestrator.services.subagents import SubagentToolset
    except Exception as exc:  # noqa: BLE001 - import failure is a check failure
        print(f"error: cannot import SubagentToolset ({exc}). Run from mcp/ with "
              f"the agent packages installed.", file=sys.stderr)
        return 1

    try:
        loaded = await SubagentToolset.load()
    except Exception as exc:  # noqa: BLE001 - any spawn/discovery failure fails the check
        print(f"error: SubagentToolset.load() failed: {exc}", file=sys.stderr)
        return 1

    tools = list(loaded.tools)
    names = [t.name for t in tools]

    print(f"discovered {len(tools)} tool(s): {names}")
    for tool in tools:
        print(f"  - {tool.name}: {_schema_of(tool)}")

    if not tools:
        print("error: tool list is EMPTY — bind_tools([]) means the model can "
              "never route to a sub-agent", file=sys.stderr)
        return 1

    if REQUIRED_TOOL not in names:
        print(f"error: required tool {REQUIRED_TOOL!r} (web_agent) is missing from "
              f"the bound set {names}", file=sys.stderr)
        return 1

    print(f"PASS: {len(tools)} tool(s) bound, {REQUIRED_TOOL!r} present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
