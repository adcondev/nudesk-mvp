# Testing Rules

## General
- Every new endpoint must have a corresponding test.
- Test file naming mirrors source: `test_<module>.py` or `<module>_test.go`.
- Integration tests go in `tests/integration/` only — never inside service directories.
- All extraction schemas must have at least one test backed by a fixture document.

## Go
- Table-driven tests with `t.Run()` subtests.
- Use testcontainers for DB-dependent tests.

## Python
- Framework: pytest + pytest-asyncio.
- Shared fixtures in `conftest.py` at each test directory level.
- Use `httpx.AsyncClient` with `ASGITransport` for FastAPI endpoint tests.
- Never mock the database in integration tests — use the real Postgres via docker-compose.
