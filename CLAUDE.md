# FinDocIQ — CLAUDE.md
 
## Project overview
 
FinDocIQ is a financial document intelligence MVP for BPO operations. Upload a PDF (bank statement, loan application, pay stub) → OCR extracts text → Claude API parses structured fields → embeddings index into pgvector → natural language RAG queries return sourced answers. All services run locally via Docker Compose. Built to demo analyst-time savings: 6 hours of manual data entry → 30 seconds.
 
## Architecture
 
| Service | Tech | Port | Directory |
|---------|------|------|-----------|
| Go API Gateway | Go, Chi, zerolog | :8080 | `gateway/` |
| Ingestion | Python, FastAPI, PaddleOCR | :8001 | `services/ingestion/` |
| Extraction + Index | Python, FastAPI, Claude API, pgvector | :8002 | `services/extraction/` |
| RAG Engine | Python, FastAPI, Claude API | :8003 | `services/rag/` |
| Demo UI | Streamlit | :8501 | `ui/` |
| Database | PostgreSQL 16 + pgvector | :5432 | `db/init.sql` |
 
## Architecture rules
 
- **Go gateway**: routing, CORS, API key auth, request ID middleware, proxy to Python services, direct DB reads via pgx. No business logic.
- **Python services**: all OCR, extraction, embedding, RAG logic. Async endpoints. Pydantic models for all request/response schemas.
- **Single database**: PostgreSQL + pgvector. Tables: `documents`, `extractions`, `chunks`. No Redis, no second datastore.
- **Inter-service**: HTTP/JSON only. No message queues in MVP. Synchronous processing flow.
- **Docker image**: Postgres uses `pgvector/pgvector:pg16` (not vanilla postgres).
 
## Domain vocabulary
 
- **document** — raw uploaded file (PDF/image), stored as metadata row + file on disk
- **document_type** — enum: `bank_statement`, `loan_application`, `pay_stub`
- **extraction** — structured JSON output from Claude API parse, stored in `extractions` table
- **chunk** — text fragment from a document, stored with embedding in pgvector
- **query** — natural language question over indexed documents
- **citation** — source chunk reference returned with RAG answer
- **derived field** — computed value (DTI, monthly_avg_income) calculated post-extraction
 
## Code conventions
 
### Go (gateway/)
- Router: Chi with middleware chain (logger → request ID → CORS → API key auth)
- Logging: zerolog (structured JSON)
- DB queries: sqlc-generated code
- Error wrapping: `fmt.Errorf("operation: %w", err)`
- Package layout: `internal/handler/`, `internal/middleware/`, `internal/types/`
 
### Python (services/)
- Framework: FastAPI with async def endpoints
- Models: Pydantic v2 (use `model_validator`, not `validator`)
- Logging: structlog (structured JSON)
- HTTP client: httpx (async)
- Migrations: alembic
- OCR: PaddleOCR (CPU mode, English)
- Embeddings: OpenAI text-embedding-3-small (1536 dims). Fallback: sentence-transformers (768 dims)
 
### API response envelope
 
All endpoints return this shape:
```json
{
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```
 
## Environment variables
 
All set in `.env` at repo root (loaded by docker-compose). See `.env.example`.
 
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://findociq:findociq@db:5432/findociq` | Postgres connection |
| `ANTHROPIC_API_KEY` | — | Claude API for extraction + RAG synthesis |
| `OPENAI_API_KEY` | — | Embeddings (text-embedding-3-small) |
| `GATEWAY_PORT` | `8080` | Go API gateway |
| `INGESTION_PORT` | `8001` | Python ingestion |
| `EXTRACTION_PORT` | `8002` | Python extraction |
| `RAG_PORT` | `8003` | Python RAG |
| `LOG_LEVEL` | `debug` | Logging level |
| `UPLOAD_DIR` | `/data/uploads` | Document storage path |
 
## Directory layout
 
```
gateway/                    # Go API gateway
  cmd/server/main.go
  internal/
    handler/                # HTTP handlers
    middleware/              # Chi middleware
    types/                  # Shared types
  go.mod
services/
  ingestion/                # Python OCR service
    app/
      main.py
      routers/
      models/
      ocr/
    requirements.txt
    Dockerfile
  extraction/               # Python extraction + indexing
    app/
      main.py
      routers/
      models/
      schemas/              # Pydantic schemas per doc type
      extractors/           # Extraction logic per doc type
    requirements.txt
    Dockerfile
  rag/                      # Python RAG query engine
    app/
      main.py
      routers/
      models/
    requirements.txt
    Dockerfile
ui/                         # Streamlit demo app
  app.py
  Dockerfile
db/
  init.sql                  # Schema: documents, extractions, chunks
migrations/                 # Alembic migrations
tests/
  fixtures/                 # Sample PDFs per doc type
  integration/              # E2E tests against running stack
docker-compose.yml
Makefile
.env.example
CLAUDE.md
```
 
## Development workflow
 
```bash
# Start everything
docker-compose up --build
 
# Verify stack
curl localhost:8080/healthz
 
# Run tests
make test          # all tests
make test-go       # Go unit tests
make test-py       # Python unit tests
make test-e2e      # integration tests (requires running stack)
 
# Migrations
make migrate       # run alembic upgrade head
 
# Linting
make lint          # go vet + ruff
```
 
## Testing conventions
 
- **Go**: table-driven tests in `_test.go` files. Use testcontainers for DB-dependent tests.
- **Python**: pytest + pytest-asyncio. Fixtures in `conftest.py`. Test files mirror source structure.
- **Integration**: tests in `tests/integration/` run against the docker-compose stack.
- **Fixtures**: sample PDFs for each document type in `tests/fixtures/`.
- **Coverage target**: not enforced for MVP, but write tests for all extraction schemas.
 
## Key constraints (MVP)
 
- Synthetic documents only — no real PII
- No production auth (API key in .env, header check)
- Single concurrent user, no load testing
- PaddleOCR cold start: 15-30s first call, ~3-8s/page after
- Synchronous processing (no job queue)
- Polling-based status updates (no WebSockets)

## Claude Code setup

The `.claude/` directory structures the AI developer workflow:
- **`commands/`** — user-invoked slash commands: `/project:new-doc-type`, `/project:review`, `/project:test-pipeline`
- **`rules/`** — auto-loaded every session: code style, testing standards, API conventions
- **`agents/`** — specialized personas: `code-reviewer` for architecture/quality gates
- **`settings.json`** — bash permissions allowlist + Postgres MCP server for live schema access
