# TASK — frontend-toolchain
owner: Engineer
immutable: true

## Requirements
- R1: Configure the frontend as a Next.js (App Router) TypeScript project, pinned to
      current latest-stable versions, using pnpm.
- R2: Dependencies (latest stable, July 2026):
  - Next.js 16.2.x (React 19.2), Tailwind CSS v4.3.x (@tailwindcss/postcss),
    Zustand 5.0.x.
  - Dev: TypeScript 5.x, ESLint 9 (eslint-config-next), Jest 30 (+ jsdom),
    Testing Library (react, jest-dom, dom, user-event).
- R3: Provide all config: package.json (scripts), tsconfig, next config,
      postcss+tailwind, eslint flat config, jest config + setup, .gitignore.
- R4: Create a Hello World page at frontend/app (App Router: layout + page + globals.css).
- R5: Provide a passing Testing Library + Jest test for the Hello World page.

## Acceptance
- A1: package.json declares all R2 deps and scripts (dev/build/start/lint/test).
- A2: Config files present and internally consistent (paths, plugins, aliases).
- A3: frontend/app renders "Hello World" (page.tsx) under a root layout with Tailwind wired.
- A4: A test asserts the Hello World heading renders.
- A5: Sandbox has no npm registry access + is Linux; node_modules is NOT shipped.
      `pnpm install` on the operator machine (macOS) resolves the lockfile.

## Constraints
- pnpm as package manager. Respect existing folder roles (app = pages only;
  tests live outside app/).
- No secrets. No business logic beyond the Hello World page + its test.
