# services/

**Role:** Services for handling API requests.

The single boundary to the backend gateway. HTTP clients, request/response mapping,
endpoint wrappers. Consumed by `shared/features`.

- Allowed: fetch/axios clients, API method wrappers, DTO mapping.
- Forbidden: React/UI code, Zustand state, business logic beyond request handling.
