# shared/features/

**Role:** Page working logic — feature modules.

All behavior that pages need: composition hooks, feature components, orchestration
of services and stores. Pages in `app/` render these; the logic lives here.

- Allowed: feature components, hooks, view-models, feature-scoped logic.
- Forbidden: raw HTTP calls (use `services/`), global store definitions (use `stores/`).
