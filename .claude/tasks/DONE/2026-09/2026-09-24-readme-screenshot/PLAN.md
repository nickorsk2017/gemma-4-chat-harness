# PLAN — 2026-09-24-readme-screenshot
plan_version: 1

## v1
- P1: Add the image as `docs/screenshot.png` (new `docs/` dir; keeps assets out of source trees).
- P2: Prepend to `README.md`: `![Gemma 4 chat UI](docs/screenshot.png)` followed by one blank line; the `# agent-chat` heading moves to line 3 unchanged.
- Risk: README.md has uncommitted edits from another change; P2 is a pure prepend and MUST NOT touch any other hunk.
