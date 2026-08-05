# TASK — 2026-07-07-novita-naming-sweep
owner: Engineer
immutable: true

## Requirements
- R1: Remove all stale "NVIDIA endpoint" naming left from the old provider:
  comments, docstrings, and the back-compat aliases NVIDIA_BASE_URL /
  DEFAULT_NVIDIA_MODEL in agent_core.llm and their imports in the four config.py.
- R2: .env.example — GEMMA_API_KEY section says Novita, not NVIDIA.
- R3: Behavior-neutral: same values, same settings fields, no API change beyond
  deleting the two aliases (used only by the configs being updated).

## Acceptance
- A1: `grep -ri nvidia` over .env.example + mcp/**/*.py returns nothing (tasks/
  excluded).
- A2: All files py_compile; configs import NOVITA_BASE_URL / DEFAULT_MODEL.
