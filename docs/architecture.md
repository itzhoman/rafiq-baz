# Architecture

Angular owns the responsive application. Desktop and native mobile platforms use identical components and business rules, rather than separately maintained screens. Capacitor packages production web assets into real Android and iOS projects.

The signal store derives visible profiles, likes, saved profiles, connections and the selected conversation. Mutations are optimistic in API mode and restore their previous state on failure. Demo mode persists to localStorage; API mode sends requests to the Python service.

The Python service stores a small JSON document per demo session in SQLite. A primary-key lookup retrieves a session; write transactions use BEGIN IMMEDIATE and WAL to avoid lost updates under concurrent requests. Input constraints are enforced with Pydantic. The API never sends messages to a real recipient.

## Boundaries

- The private hosted review is a static Angular build with local demo state.
- The local server on port 8000 serves the built app and the Python API from one origin.
- The Android and iOS projects bundle assets and run the local sample without requiring an API.
- CORS allows only the local development and Capacitor origins.
- Session UUIDs are not login credentials. Python accounts resolve through hashed server-side session tokens in HttpOnly cookies; their state is stored under a separate account namespace. See accounts.md for security properties and deployment boundaries.
- Profile verification badges and online indicators are sample data, not live identity or presence checks.
- The version is intended for design review. Email account auth is available on Python; Google requires external configuration. Moderation, reporting/blocking, real-time messaging, location consent, media uploads and full production privacy controls are not implemented.

## Growth

The relationship-focused finder uses a small pure TypeScript recommendation module. Angular signals recompute only when profiles or relevant state change. Feedback is stored separately from passes, and custom attributes have matching frontend/API validation. See finding.md for the explicit ranking and similarity rules.

The frontend consumes typed data through the store; the UI does not query SQLite directly. Auth UI is deferred until opened. The 110-profile fixture loads as a separate JSON resource rather than expanding the initial JavaScript; its original vector avatars are local, lazy-cached assets. The generator is scripts/generate-demo-profiles.py. Move beyond SQLite only after actual access patterns and hosting requirements justify it.
