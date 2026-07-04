# TASK — frontend-scaffold
owner: Engineer
immutable: true

## Requirements
- R1: Create the `frontend/` directory tree with these roles:
  - `frontend/app` — pages only, no logic/business code; SSR entrypoints.
  - `frontend/shared/features` — page working logic (feature modules).
  - `frontend/shared/ui-kit` — Design System components.
  - `frontend/services` — API request handling services.
  - `frontend/stores` — Zustand stores.
  - `frontend/types` — `*.d.ts` type declarations for all entities.
- R2: Every leaf folder is committable when empty (keep-file present).
- R3: Every leaf folder documents its purpose + allowed/forbidden contents (README.md).

## Acceptance
- A1: All six paths in R1 exist under `frontend/`.
- A2: Each leaf folder has a keep-file so git tracks it empty.
- A3: Each leaf folder has a README.md stating its single responsibility.
- A4: No application/business code is added in this task (structure only).

## Constraints
- Scope is scaffolding only: directories, keep-files, per-folder README.md.
- Do not create build config, deps, or components yet.
- Boundaries: `app` holds no logic; logic lives in `shared/features`.
