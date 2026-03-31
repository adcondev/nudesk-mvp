# Code Style Rules

## Go (gateway/)
- Logging: zerolog only. Never `fmt.Println` or `log.Print`.
- Error wrapping: `fmt.Errorf("noun phrase: %w", err)` — not "failed to...".
- Handler signatures: `func(w http.ResponseWriter, r *http.Request)`.
- Always `defer r.Body.Close()` when reading request bodies.
- Package imports: stdlib first, then external, then internal — separated by blank lines.

## Python (services/)
- All FastAPI endpoints must be `async def`.
- Type hints on every function signature — parameters and return type.
- Pydantic v2 only: `model_validator` not `validator`, `model_dump()` not `.dict()`.
- Logging: structlog only. Never bare `print()`.
- Use `httpx.AsyncClient` for outbound HTTP, never `requests`.

## Both languages
- No hardcoded ports, URLs, or credentials — always env vars.
- No magic numbers — use named constants or config values.
- Max function length: 50 lines. Split if longer.
