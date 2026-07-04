# PLAN — frontend-scaffold

plan_version: 1

## Target tree (leaf folders)
- P1 frontend/app                → SSR pages, no logic (R1)
- P2 frontend/shared/features    → feature/page logic (R1)
- P3 frontend/shared/ui-kit      → Design System (R1)
- P4 frontend/services           → API request services (R1)
- P5 frontend/stores             → Zustand stores (R1)
- P6 frontend/types              → *.d.ts entity declarations (R1)

## Approach
- S1: Create the six leaf dirs (P1–P6). `shared/` is a grouping node, not a leaf.
- S2: Each leaf gets `.gitkeep` (R2, A2) so empty dirs are tracked by git.
- S3: Each leaf gets `README.md` stating single responsibility + allowed/forbidden
      contents (R3, A3). Encode the boundary rule: logic in features, never in app.
- S4: No code/config/deps (A4). Structure only.

## Sequencing
mkdir -p (S1) → write keep-files (S2) → write READMEs (S3). Order independent per leaf.

## Risks
- Empty dirs vanish in git without keep-files → S2 mitigates.
- `app` accreting logic → README boundary note (S3) documents the rule for later tasks.

## Out of scope (future tasks)
Next.js/Tailwind/Zustand install, tsconfig, frontend/CLAUDE.md, actual components.
