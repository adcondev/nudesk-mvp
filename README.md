# FinDocIQ

Upload a financial PDF, get structured data and natural language answers in seconds. Built to demo BPO analyst-time savings: 6 hours of manual data entry → 30 seconds.

## Quickstart

**Prerequisites:** Docker + Docker Compose v2, API keys for Anthropic and OpenAI.

```bash
# 1. Clone the repo
git clone <repo-url> && cd nudesk-mvp

# 2. Configure environment
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and OPENAI_API_KEY

# 3. Start the stack
docker-compose up --build

# 4. Open the demo UI
open http://localhost:8501
```

First OCR call takes 15–30 seconds (PaddleOCR cold start). Subsequent calls: 3–8s per page.

## Architecture

```
Demo UI (Streamlit :8501)
        │
        ▼
Go API Gateway (Chi :8080)
   ├── POST /ingest        → Ingestion Service (:8001)  — PaddleOCR
   ├── GET  /documents/:id → PostgreSQL direct (pgx)
   ├── GET  /documents     → PostgreSQL direct (pgx)
   └── POST /query         → RAG Engine (:8003)         — Claude API
                                     ↑
                           Extraction Service (:8002)   — Claude API + OpenAI Embeddings
                                     │
                               PostgreSQL 16 + pgvector
                               (documents · extractions · chunks)
```

| Service | Tech | Port |
|---------|------|------|
| Go API Gateway | Go, Chi, zerolog | 8080 |
| Ingestion | Python, FastAPI, PaddleOCR | 8001 |
| Extraction + Index | Python, FastAPI, Claude API, pgvector | 8002 |
| RAG Engine | Python, FastAPI, Claude API | 8003 |
| Demo UI | Streamlit | 8501 |
| Database | PostgreSQL 16 + pgvector | 5432 |

## Supported Document Types

| Type | Extracted Fields | Derived Metrics |
|------|-----------------|-----------------|
| `bank_statement` | account number, holder name, statement date, total deposits/withdrawals, ending balance | total deposits snapshot |
| `loan_application` | applicant name, SSN, loan amount, monthly gross income, monthly debt payments | DTI ratio |
| `pay_stub` | employee/employer name, pay period, gross pay, net pay, YTD gross, taxes withheld | effective tax rate, monthly income proxy |

## Demo Script

1. **Upload a bank statement** → watch status polling → see extracted fields table
2. **Check risk flags panel** → no red flags on a clean statement
3. **Upload a loan application** → see DTI metric (red if > 43%)
4. **Ask**: "What is the applicant's name and SSN?"
5. **Ask**: "Summarize the income and debt obligations."
6. Expand **View Sources** → see the exact text chunks that grounded the answer

## API Reference

All endpoints require `Authorization: Bearer <API_KEY>` header. All responses use the envelope format:

```json
{ "data": {}, "error": null, "meta": { "request_id": "uuid", "timestamp": "ISO8601" } }
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Stack health (DB + downstream services) |
| POST | `/ingest` | Upload PDF (multipart/form-data `file` field) |
| GET | `/documents` | List all documents |
| GET | `/documents/:id` | Get document status + extracted data |
| POST | `/query` | RAG query `{"query": "..."}` |

## Running Tests

```bash
make test        # Go unit tests + Python unit tests
make test-e2e    # Integration tests (requires running stack)
make lint        # go vet + ruff
```

## Environment Variables

See `.env.example` for all variables. Key ones to set:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key (extraction + RAG synthesis) |
| `OPENAI_API_KEY` | OpenAI key (text-embedding-3-small) |
| `API_KEY` | Gateway auth key (default: `changeme`) |

## Tech Decisions

- **Go gateway, Python services** — Go for routing/proxying; Python for PaddleOCR, sentence-transformers, Anthropic SDK (no Go equivalents).
- **pgvector over Chroma/Pinecone** — single DB dependency; colocates structured extractions and vector embeddings; HNSW index is production-grade.
- **Claude API for extraction** — prompt-based extraction generalises across layout variations instantly; regex breaks on any format change; fine-tuning needs weeks of labelled data.
- **PaddleOCR over Tesseract** — fully local (no API costs), outperforms Tesseract on modern printed docs, handles rotated text.
- **Streamlit for UI** — demo surface produced in hours; React is the natural production replacement.

## Known Limitations

- **No production auth** — API key in `.env`, header comparison only. Production needs OAuth2 + RBAC.
- **Synchronous processing** — no job queue. Under load, long OCR jobs block the worker. Production needs Celery/Redis.
- **PaddleOCR cold start** — 15–30s on first call per container restart.
- **Polling-based status** — UI polls every 2s. Production would use WebSockets or SSE.
- **No PII redaction** — raw OCR text (names, SSNs) stored in plaintext. Production needs a redaction layer.
- **Streamlit is a demo surface only** — not suitable for multi-user production deployment.
- **Synthetic documents only** — no real PII used in development or testing.
