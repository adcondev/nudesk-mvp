# API Conventions

## Response envelope (all endpoints)
```json
{
  "data": { ... },
  "error": null,
  "meta": { "request_id": "uuid", "timestamp": "ISO8601" }
}
```
On error: `"data": null`, `"error": { "code": "string", "message": "string" }`.

## URL design
- Pattern: `/api/v1/<plural-noun>` — e.g., `/api/v1/documents`, `/api/v1/queries`.
- No verbs in URLs. Use HTTP methods for actions.
- Resource IDs in path: `/api/v1/documents/{id}`.

## Status codes
- 200: success (GET, POST actions)
- 201: resource created (POST upload)
- 400: validation error
- 404: resource not found
- 500: server error

## Headers
- `X-Request-ID`: generated at gateway, propagated to all downstream services.
- `Content-Type: application/json` on all non-file responses.

## Health checks
- Every service exposes `GET /healthz` returning `{"status": "ok"}`.
- Gateway `/healthz` checks Postgres + downstream service availability.
