# app/

**Role:** Pages only — SSR entrypoints. No logic, no business code.

Route/segment files, layouts, and server components that compose UI from
`shared/features` and `shared/ui-kit`. This folder wires pages together; it does
not implement behavior.

- Allowed: Next.js `app/` routes, layouts, `page.tsx`, `loading.tsx`, `error.tsx`, metadata.
- Forbidden: business logic, data fetching implementations, state — import those from `../shared/features`, `../services`, `../stores`.
