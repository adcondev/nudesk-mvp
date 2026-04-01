# FinDocIQ — Technical Details Guide

**Financial Document Intelligence Platform — Architecture, Modules, and Operations**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Prerequisites](#2-prerequisites)
3. [Step-by-Step Setup Guide](#3-step-by-step-setup-guide)
4. [Architecture Overview](#4-architecture-overview)
5. [Module & Submodule Breakdown](#5-module--submodule-breakdown)
6. [Data Flow Diagrams](#6-data-flow-diagrams)
7. [API Reference](#7-api-reference)
8. [Database Schema Reference](#8-database-schema-reference)
9. [Configuration Reference](#9-configuration-reference)
10. [Development Workflow](#10-development-workflow)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Executive Summary

FinDocIQ is a microservices-based MVP that automates financial document processing for BPO operations. The system receives a PDF upload (bank statement, loan application, or pay stub), runs OCR via PaddleOCR to extract raw text, sends that text to the Claude API for structured field extraction, generates vector embeddings via OpenAI, indexes chunks into PostgreSQL with pgvector, and exposes a natural-language RAG query interface that returns sourced answers.

**Value proposition:** 6 hours of manual data entry reduced to 30 seconds.

**Tech stack at a glance:**

| Layer | Technology |
|-------|-----------|
| API Gateway | Go 1.23, Chi router, zerolog |
| OCR & Ingestion | Python 3.12, FastAPI, PaddleOCR |
| Extraction & Indexing | Python 3.12, FastAPI, Claude API, OpenAI Embeddings |
| RAG Query Engine | Python 3.12, FastAPI, Claude API, pgvector |
| Demo UI | Streamlit |
| Database | PostgreSQL 16 + pgvector (HNSW index) |
| Orchestration | Docker Compose |

---

## 2. Prerequisites

Before running the project, ensure you have:

| Requirement | Details |
|-------------|---------|
| **Docker Desktop** | Or Docker Engine + Docker Compose v2. Required to run all services. |
| **Anthropic API Key** | Required for Claude-based extraction and RAG synthesis. Get one at https://console.anthropic.com/ |
| **OpenAI API Key** | Required for text-embedding-3-small embeddings. Get one at https://platform.openai.com/ |
| **RAM** | Minimum 8 GB recommended. PaddleOCR loads ML models into memory. |
| **Disk space** | ~4 GB for Docker images (PaddleOCR image is large). |

> **Note:** You do NOT need Go or Python installed locally. Everything runs inside Docker containers.

---

## 3. Step-by-Step Setup Guide

### 3.1 Clone the Repository

```bash
git clone https://github.com/<your-org>/nudesk-mvp.git
cd nudesk-mvp
```

### 3.2 Configure Environment Variables

Copy the example file and fill in your API keys:

```bash
cp .env.example .env
```

Open `.env` in your editor. The file contains these variables:

| Variable | Default | Required | What to Edit |
|----------|---------|----------|-------------|
| `DATABASE_URL` | `postgresql://findociq:findociq@db:5432/findociq` | No | Leave as-is (uses Docker internal hostname `db`) |
| `ANTHROPIC_API_KEY` | *(empty)* | **YES** | Paste your Anthropic API key (e.g., `sk-ant-...`) |
| `OPENAI_API_KEY` | *(empty)* | **YES** | Paste your OpenAI API key (e.g., `sk-...`) |
| `GATEWAY_PORT` | `8080` | No | Change only if port 8080 is in use |
| `INGESTION_PORT` | `8001` | No | Change only if port 8001 is in use |
| `EXTRACTION_PORT` | `8002` | No | Change only if port 8002 is in use |
| `RAG_PORT` | `8003` | No | Change only if port 8003 is in use |
| `LOG_LEVEL` | `debug` | No | Set to `info` for less verbose logs |
| `UPLOAD_DIR` | `/data/uploads` | No | Container-internal path. Leave as-is. |
| `EXTRACTION_MODEL` | `claude-opus-4-6` | No | Claude model for extraction. Change if needed. |
| `API_KEY` | `changeme` | **Recommended** | Bearer token for gateway auth. Change for security. |

**Critical:** The two API keys (`ANTHROPIC_API_KEY` and `OPENAI_API_KEY`) are mandatory. Without them, extraction and RAG will fail.

### 3.3 Build and Start All Services

```bash
docker compose up --build
```

Or use the Makefile shortcuts:

```bash
make build    # Build all images
make up       # Start in detached mode
make logs     # Stream logs
```

**Startup order** (Docker Compose handles this automatically):

```
db (PostgreSQL + pgvector)
  ├─ Waits for: pg_isready health check
  │
  ├──> gateway (Go API)
  │      ├─ Waits for: db healthy
  │      └──> ui (Streamlit)
  │             └─ Waits for: gateway healthy
  │
  ├──> ingestion (Python OCR)
  │      └─ Waits for: db healthy
  │
  ├──> extraction (Python Claude + embeddings)
  │      └─ Waits for: db healthy
  │
  ├──> rag (Python RAG engine)
  │      └─ Waits for: db healthy
  │
  └──> adminer (DB web UI)
         └─ Waits for: db healthy
```

> **First startup** takes 3-5 minutes to pull images and build containers. Subsequent starts are much faster.

### 3.4 Verify the Stack

Check that all services are healthy:

```bash
curl http://localhost:8080/healthz
```

Expected response:

```json
{
  "status": "ok",
  "db": "up",
  "ingestion": "up",
  "rag": "up"
}
```

### 3.5 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Demo UI** | http://localhost:8501 | Main user interface — upload, view extractions, query |
| **Gateway API** | http://localhost:8080 | REST API for all operations |
| **Adminer** | http://localhost:8081 | Database browser (login: `findociq` / `findociq`, server: `db`) |

### 3.6 Upload a Test Document

**Via the UI:**
1. Open http://localhost:8501
2. Click "Browse files" and select a PDF (bank statement, loan application, or pay stub)
3. Click "Upload & Process"
4. Wait for the status to show "completed" (30-60 seconds)

**Via cURL:**

```bash
curl -X POST http://localhost:8080/documents \
  -H "Authorization: Bearer changeme" \
  -F "file=@path/to/your/document.pdf"
```

Response:

```json
{
  "data": { "document_id": "abc-123-...", "status": "pending" },
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

Then poll for completion:

```bash
curl http://localhost:8080/documents/<document_id> \
  -H "Authorization: Bearer changeme"
```

### 3.7 Query via RAG

Once documents are processed, ask questions:

```bash
curl -X POST http://localhost:8080/query \
  -H "Authorization: Bearer changeme" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the ending balance?"}'
```

Response:

```json
{
  "data": {
    "answer": "Based on the bank statement, the ending balance is $12,345.67.",
    "sources": [
      {
        "id": "...",
        "document_id": "...",
        "chunk_index": 3,
        "content": "Ending Balance: $12,345.67...",
        "distance": 0.1234
      }
    ]
  },
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

### 3.8 Teardown

```bash
docker compose down          # Stop services (preserves data)
make clean                   # Stop + remove volumes + uploads (full reset)
```

---

## 4. Architecture Overview

### 4.1 High-Level Architecture Diagram

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                         CLIENTS                                     │
 │   ┌──────────┐    ┌──────────────────┐    ┌──────────────────┐     │
 │   │  cURL /  │    │   Streamlit UI   │    │    Adminer       │     │
 │   │  Postman │    │   :8501          │    │    DB UI :8081   │     │
 │   └────┬─────┘    └───────┬──────────┘    └────────┬─────────┘     │
 └────────│──────────────────│────────────────────────│────────────────┘
          │                  │                        │
          ▼                  ▼                        │
 ┌────────────────────────────────────┐               │
 │       Go API Gateway :8080        │               │
 │  ┌──────────────────────────────┐ │               │
 │  │ Chi Router + Middleware      │ │               │
 │  │ ┌─────────┐ ┌────────────┐  │ │               │
 │  │ │RequestID│ │  API Key   │  │ │               │
 │  │ │  CORS   │ │   Auth     │  │ │               │
 │  │ └─────────┘ └────────────┘  │ │               │
 │  └──────────────────────────────┘ │               │
 │                                   │               │
 │  GET /documents ──> Direct DB     │               │
 │  POST /documents ─> Proxy        │               │
 │  POST /query ─────> Proxy        │               │
 └───────┬──────────┬───────────┬───┘               │
         │          │           │                    │
    ┌────┘     ┌────┘           └────┐               │
    ▼          ▼                     ▼               │
 ┌──────────┐ ┌──────────────┐ ┌──────────┐         │
 │Ingestion │ │  Extraction  │ │   RAG    │         │
 │  :8001   │ │   :8002      │ │  :8003   │         │
 │          │ │              │ │          │         │
 │PaddleOCR │ │ Claude API   │ │Claude API│         │
 │pdf2image │ │ OpenAI Emb.  │ │OpenAI Emb│         │
 └────┬─────┘ └──────┬───────┘ └────┬─────┘         │
      │               │              │               │
      │          ┌────┘              │               │
      ▼          ▼                   ▼               │
 ┌───────────────────────────────────────────┐       │
 │     PostgreSQL + pgvector :5432           │◄──────┘
 │                                           │
 │  ┌───────────┐ ┌─────────────┐ ┌───────┐ │
 │  │ documents │ │ extractions │ │chunks │ │
 │  │           │ │  (JSONB)    │ │(vec)  │ │
 │  └───────────┘ └─────────────┘ └───────┘ │
 │          HNSW index on embeddings         │
 └───────────────────────────────────────────┘
```

### 4.2 Service Communication Matrix

| From | To | Protocol | Endpoint | Purpose |
|------|----|----------|----------|---------|
| UI | Gateway | HTTP | `POST /documents` | Upload document |
| UI | Gateway | HTTP | `GET /documents/{id}` | Poll extraction status |
| UI | Gateway | HTTP | `POST /query` | RAG query |
| Gateway | Ingestion | HTTP (reverse proxy) | `POST /ingest` | Forward file upload |
| Gateway | RAG | HTTP (reverse proxy) | `POST /query` | Forward RAG query |
| Gateway | PostgreSQL | TCP (pgx) | SQL queries | List/get documents |
| Ingestion | Extraction | HTTP | `POST /extract` | Trigger extraction after OCR |
| Ingestion | PostgreSQL | TCP (SQLAlchemy) | SQL queries | Store document metadata + OCR text |
| Extraction | PostgreSQL | TCP (asyncpg) | SQL queries | Read raw_text, store extractions + chunks |
| Extraction | Claude API | HTTPS | Anthropic SDK | Extract structured fields |
| Extraction | OpenAI API | HTTPS | OpenAI SDK | Generate embeddings |
| RAG | PostgreSQL | TCP (asyncpg) | SQL queries | Vector similarity search |
| RAG | Claude API | HTTPS | Anthropic SDK | Synthesize answers |
| RAG | OpenAI API | HTTPS | OpenAI SDK | Embed user query |

### 4.3 Authentication Flow

```
Client Request
    │
    ▼
┌──────────────────────────────┐
│  GET /healthz ?              │
│  ├── YES → Skip auth → 200  │
│  └── NO  → Continue         │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  API_KEY env var set?        │
│  ├── NO → Log warning,      │
│  │        allow all (auth    │
│  │        disabled)          │
│  └── YES → Continue         │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Authorization header        │
│  has "Bearer <token>"?       │
│  ├── NO → 401 Unauthorized   │
│  └── YES → Continue         │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Token matches API_KEY?      │
│  ├── NO → 401 Unauthorized   │
│  └── YES → Allow request    │
└──────────────────────────────┘
```

---

## 5. Module & Submodule Breakdown

### 5.1 Database Layer

**Location:** `db/init.sql`

The database runs on PostgreSQL 16 with the pgvector extension for vector similarity search.

#### Enums

| Enum | Values |
|------|--------|
| `document_type` | `bank_statement`, `loan_application`, `pay_stub` |
| `document_status` | `pending`, `processing`, `completed`, `failed` |

#### Entity-Relationship Diagram

```
┌──────────────────────────────┐
│          documents           │
├──────────────────────────────┤
│ id           UUID PK         │
│ filename     TEXT NOT NULL    │
│ document_type  ENUM          │
│ status       ENUM (pending)  │
│ file_path    TEXT            │
│ raw_text     TEXT            │
│ page_count   INTEGER        │
│ uploaded_at  TIMESTAMPTZ    │
│ updated_at   TIMESTAMPTZ    │
└──────────┬───────────────────┘
           │ 1
           │
     ┌─────┴──────┐
     │             │
     ▼ N           ▼ N
┌────────────────┐  ┌──────────────────────────┐
│  extractions   │  │         chunks           │
├────────────────┤  ├──────────────────────────┤
│ id       UUID PK│  │ id           UUID PK     │
│ document_id  FK │  │ document_id  FK          │
│ extracted_data  │  │ chunk_index  INT         │
│   JSONB        │  │ content      TEXT        │
│ confidence_    │  │ embedding    vector(1536)│
│   scores JSONB │  │ metadata     JSONB       │
│ model_version  │  │ created_at   TIMESTAMPTZ │
│   TEXT         │  ├──────────────────────────┤
│ created_at     │  │ UNIQUE(document_id,      │
│   TIMESTAMPTZ  │  │        chunk_index)      │
└────────────────┘  └──────────────────────────┘
```

#### Indexes

| Index | Type | Table | Column(s) | Purpose |
|-------|------|-------|-----------|---------|
| `idx_chunks_embedding` | HNSW | chunks | embedding (cosine) | Fast approximate nearest neighbor search |
| `idx_extractions_data` | GIN | extractions | extracted_data | JSONB field queries |
| `idx_documents_status` | B-tree | documents | status | Filter by processing status |
| `idx_documents_type` | B-tree | documents | document_type | Filter by document type |
| `idx_extractions_doc` | B-tree | extractions | document_id | Foreign key lookups |
| `idx_chunks_doc` | B-tree | chunks | document_id | Foreign key lookups |

#### Trigger

`update_documents_modtime` — automatically sets `updated_at = NOW()` whenever a `documents` row is modified.

---

### 5.2 Gateway Service (Go)

**Location:** `gateway/`
**Port:** 8080
**Tech:** Go 1.23, Chi router, pgx connection pool, zerolog

#### File Structure

```
gateway/
├── cmd/server/
│   └── main.go                 # Entry point, router setup
├── internal/
│   ├── handler/
│   │   ├── document.go         # ListDocuments, GetDocument
│   │   └── health.go           # Aggregated health check
│   ├── middleware/
│   │   └── auth.go             # Bearer token authentication
│   └── types/
│       └── response.go         # Envelope struct + helpers
├── go.mod
├── go.sum
└── Dockerfile                  # Multi-stage build (golang:1.23-alpine → alpine:3.20)
```

#### Submodule Details

**`cmd/server/main.go`** — Application entry point
- Reads environment variables (`GATEWAY_PORT`, `DATABASE_URL`, service URLs)
- Creates pgxpool connection pool to PostgreSQL
- Builds reverse proxies for ingestion (`http://ingestion:8001`) and RAG (`http://rag:8003`)
- Configures Chi middleware chain: RequestID → RealIP → Logger → Recoverer → CORS → APIKeyAuth
- CORS allows origin `http://localhost:8501` (Streamlit UI)
- Registers all routes and starts HTTP server

**`internal/middleware/auth.go`** — API Key authentication
- Exempts `GET /healthz` from authentication
- Reads `API_KEY` from environment; if unset, logs a warning and allows all requests
- Validates `Authorization: Bearer <token>` header against `API_KEY`
- Returns 401 Unauthorized on mismatch

**`internal/handler/document.go`** — Document query handlers
- `ListDocuments`: queries last 50 documents ordered by `uploaded_at DESC` directly from PostgreSQL (no Python service call)
- `GetDocument`: fetches a single document by UUID, JOINs with `extractions` table to include `extracted_data` in the response

**`internal/handler/health.go`** — Aggregated health check
- Pings PostgreSQL with 2-second timeout
- Calls `GET /healthz` on ingestion and RAG services
- Returns overall status: `ok` if all healthy, `error` (HTTP 503) if any service is down

**`internal/types/response.go`** — Standard response envelope
- `Envelope` struct: `{ data, error, meta: { request_id, timestamp } }`
- `WriteJSON()`: wraps success data in envelope
- `WriteError()`: wraps error in envelope with null data

#### Route Table

| Method | Path | Auth | Handler | Description |
|--------|------|------|---------|-------------|
| GET | `/healthz` | No | `HealthCheck` | Aggregated health of DB + services |
| GET | `/documents` | Yes | `ListDocuments` | Last 50 documents (direct DB) |
| GET | `/documents/{id}` | Yes | `GetDocument` | Single document + extraction (direct DB) |
| POST | `/documents` | Yes | Reverse proxy → Ingestion `/ingest` | Upload PDF for processing |
| POST | `/query` | Yes | Reverse proxy → RAG `/query` | Natural language RAG query |

#### Dockerfile

Multi-stage build for minimal image size:
1. **Builder:** `golang:1.23-alpine` — compiles static binary (`CGO_ENABLED=0`)
2. **Runtime:** `alpine:3.20` — runs the binary (~15 MB final image)

---

### 5.3 Ingestion Service (Python)

**Location:** `services/ingestion/`
**Port:** 8001
**Tech:** FastAPI, PaddleOCR 2.7.3, pdf2image, SQLAlchemy (sync)

#### File Structure

```
services/ingestion/
├── app/
│   └── main.py                 # FastAPI app, OCR pipeline
├── requirements.txt
└── Dockerfile                  # python:3.12-slim + poppler-utils + OpenGL libs
```

#### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/ingest` | Accept PDF upload, start OCR pipeline |
| GET | `/healthz` | Service health check |

#### Submodule Details

**`app/main.py`** — Core ingestion logic

- **PaddleOCR initialization:** `PaddleOCR(use_angle_cls=True, lang='en')` — loads English model with angle classification for rotated text
- **Upload handler (`POST /ingest`):**
  - Validates file is a PDF
  - Generates UUID for document
  - Saves file to `{UPLOAD_DIR}/{document_id}.pdf`
  - Inserts `documents` row with `status=pending`
  - Launches background task `process_document()`

- **Background processing pipeline:**

```
PDF File on Disk
       │
       ▼
┌─────────────────────────┐
│  pdf2image               │
│  Convert PDF → PNG/page  │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  PaddleOCR               │
│  Extract text per page   │
│  (runs in thread pool)   │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Concatenate all text    │
│  Count pages             │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Document Type Detection │
│  (keyword heuristic)     │
│                          │
│  "pay stub" or           │
│  "earnings" → pay_stub   │
│                          │
│  "loan application"      │
│              → loan_app  │
│                          │
│  default → bank_statement│
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Update DB               │
│  status = processing     │
│  raw_text, doc_type,     │
│  page_count              │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  POST /extract           │
│  → Extraction Service    │
│  payload: {document_id}  │
│  timeout: 60s            │
└─────────────────────────┘
```

#### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.110.0 | Web framework |
| uvicorn | 0.29.0 | ASGI server |
| paddleocr | 2.7.3 | OCR engine |
| paddlepaddle | 2.6.1 | ML framework for PaddleOCR |
| pdf2image | 1.17.0 | PDF to image conversion |
| sqlalchemy | 2.0.29 | Database ORM (sync) |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| httpx | 0.27.0 | Async HTTP client |
| structlog | 24.1.0 | Structured logging |
| python-multipart | 0.0.9 | Form/file upload parsing |

#### Dockerfile Notes

- Base: `python:3.12-slim`
- System packages: `poppler-utils` (PDF rendering), `libgl1`, `libglib2.0-0`, `libgomp1` (OpenGL/threading for PaddleOCR)
- PaddleOCR downloads its model (~100MB) on first use inside the container

---

### 5.4 Extraction Service (Python)

**Location:** `services/extraction/`
**Port:** 8002
**Tech:** FastAPI, Anthropic SDK, OpenAI SDK, SQLAlchemy (async), pgvector

#### File Structure

```
services/extraction/
├── app/
│   └── main.py                 # FastAPI app, extraction + embedding logic
├── requirements.txt
└── Dockerfile                  # python:3.12-slim
```

#### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/extract` | Start extraction for a document (background task) |
| GET | `/healthz` | Service health check |

#### Pydantic Models

**BankStatementExtraction:**

| Field | Type | Description |
|-------|------|-------------|
| account_number | Optional[str] | Bank account number |
| account_holder_name | Optional[str] | Name on the account |
| statement_date | Optional[str] | Statement period date |
| total_deposits | Optional[float] | Sum of all deposits |
| total_withdrawals | Optional[float] | Sum of all withdrawals |
| ending_balance | Optional[float] | Closing balance |

**LoanApplicationExtraction:**

| Field | Type | Description |
|-------|------|-------------|
| applicant_name | Optional[str] | Borrower name |
| social_security_number | Optional[str] | SSN |
| loan_amount | Optional[float] | Requested loan amount |
| monthly_gross_income | Optional[float] | Monthly income before taxes |
| monthly_debt_payments | Optional[float] | Monthly debt obligations |
| calculated_dti | Optional[float] | Debt-to-income ratio |

**PayStubExtraction:**

| Field | Type | Description |
|-------|------|-------------|
| employee_name | Optional[str] | Employee name |
| employer_name | Optional[str] | Company name |
| pay_period_start | Optional[str] | Pay period start date |
| pay_period_end | Optional[str] | Pay period end date |
| gross_pay | Optional[float] | Gross earnings |
| net_pay | Optional[float] | Take-home pay |
| ytd_gross | Optional[float] | Year-to-date gross |
| taxes_withheld | Optional[float] | Total taxes deducted |

#### Extraction Pipeline

```
POST /extract {document_id}
       │
       ▼
┌─────────────────────────────┐
│  Fetch from DB               │
│  SELECT raw_text,            │
│         document_type        │
│  FROM documents              │
│  WHERE id = {document_id}    │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Build type-specific prompt  │
│                              │
│  Bank Statement → 6 fields   │
│  Loan Application → 6 fields│
│  Pay Stub → 8 fields        │
│                              │
│  Prompt: "Extract these      │
│  fields as JSON only..."     │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Claude API Call             │
│  Model: claude-opus-4-6      │
│  Temperature: 0              │
│  Max tokens: 1000            │
│  System: "Expert at          │
│  extracting structured data  │
│  from financial documents"   │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Parse JSON Response         │
│  Strip markdown fences       │
│  Validate with Pydantic      │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Compute Derived Fields      │
│                              │
│  Bank Statement:             │
│    total_deposits_snapshot   │
│    dti: null                 │
│                              │
│  Loan Application:           │
│    dti = debt / income       │
│                              │
│  Pay Stub:                   │
│    effective_tax_rate_pct    │
│      = (taxes/gross) × 100  │
│    monthly_income_proxy      │
│      = gross × 2 (biweekly) │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Chunk & Embed               │
│                              │
│  Split raw_text on "\n\n"    │
│  → paragraphs               │
│                              │
│  OpenAI Embeddings API       │
│  Model: text-embedding-      │
│         3-small              │
│  Dimensions: 1536            │
│                              │
│  INSERT INTO chunks          │
│  (document_id, chunk_index,  │
│   content, embedding)        │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Store Extraction            │
│  INSERT INTO extractions     │
│  (extracted_data, model_ver) │
│                              │
│  UPDATE documents            │
│  SET status = 'completed'    │
└─────────────────────────────┘
```

#### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.110.0 | Web framework |
| uvicorn | 0.29.0 | ASGI server |
| anthropic | 0.25.1 | Claude API client |
| openai | 1.14.3 | OpenAI embeddings client |
| pydantic | 2.6.4 | Data validation (v2) |
| sqlalchemy | 2.0.29 | Async ORM |
| asyncpg | latest | Async PostgreSQL driver |
| pgvector | latest | Vector column type for SQLAlchemy |
| structlog | 24.1.0 | Structured logging |
| httpx | 0.27.0 | Async HTTP client |

---

### 5.5 RAG Service (Python)

**Location:** `services/rag/`
**Port:** 8003
**Tech:** FastAPI, Anthropic SDK, OpenAI SDK, SQLAlchemy (async), pgvector

#### File Structure

```
services/rag/
├── app/
│   └── main.py                 # FastAPI app, RAG pipeline
├── requirements.txt
└── Dockerfile                  # python:3.12-slim
```

#### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/query` | Execute RAG query over indexed documents |
| GET | `/healthz` | Service health check |

#### RAG Pipeline

```
User Query: "What is the ending balance?"
       │
       ▼
┌─────────────────────────────┐
│  Embed Query                 │
│  OpenAI text-embedding-      │
│  3-small → 1536-dim vector   │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Vector Similarity Search    │
│                              │
│  SELECT id, document_id,     │
│    chunk_index, content,     │
│    embedding <=> :query      │
│    AS distance               │
│  FROM chunks                 │
│  ORDER BY distance ASC       │
│  LIMIT 5                     │
│                              │
│  Operator: <=> (cosine dist) │
│  Index: HNSW (approximate)   │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Build Context               │
│                              │
│  "Source 1:                   │
│   {chunk_1_content}          │
│                              │
│   Source 2:                   │
│   {chunk_2_content}          │
│   ..."                       │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Claude Synthesis            │
│  Model: claude-opus-4-6      │
│  Temperature: 0              │
│  System: "Expert financial   │
│  assistant"                  │
│                              │
│  User: "Use context to       │
│  answer. If not found, say   │
│  'I don't know...'"         │
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│  Return Response             │
│  {                           │
│    answer: "The ending...",  │
│    sources: [                │
│      { id, document_id,     │
│        chunk_index, content, │
│        distance }            │
│    ]                         │
│  }                           │
└─────────────────────────────┘
```

#### Dependencies

Same as the extraction service (anthropic, openai, sqlalchemy, asyncpg, pgvector, structlog, httpx).

---

### 5.6 UI Service (Streamlit)

**Location:** `ui/`
**Port:** 8501
**Tech:** Streamlit 1.32.0, httpx

#### File Structure

```
ui/
├── app.py                      # Streamlit application
├── requirements.txt
└── Dockerfile                  # python:3.12-slim + streamlit
```

#### Application Layout

The UI is a single-page Streamlit app with two main sections:

**Section 1: Upload & Process**

```
┌──────────────────────────────────────────────────┐
│  📄 FinDocIQ Demo                                │
│                                                   │
│  ┌──────────────────────────────────────┐        │
│  │  [Browse files]  Choose a PDF file   │        │
│  └──────────────────────────────────────┘        │
│  [ Upload & Process ]                            │
│                                                   │
│  Status: ● Completed                              │
│                                                   │
│  ┌─────────────────────┬─────────────────────┐   │
│  │  Extracted Fields    │  Key Metrics        │   │
│  │                      │                     │   │
│  │  account_number:     │  DTI: 35.2%  ✓     │   │
│  │    1234-5678         │                     │   │
│  │  ending_balance:     │  Monthly Income:    │   │
│  │    $12,345.67        │    $5,200           │   │
│  │  total_deposits:     │                     │   │
│  │    $8,500.00         │  Risk Flags:        │   │
│  │  ...                 │    (none)           │   │
│  └─────────────────────┴─────────────────────┘   │
└──────────────────────────────────────────────────┘
```

**Section 2: RAG Query**

```
┌──────────────────────────────────────────────────┐
│  Ask a Question                                   │
│                                                   │
│  Quick queries:                                   │
│  [Applicant name & SSN] [Income & debt] [Deposits]│
│                                                   │
│  ┌──────────────────────────────────────┐        │
│  │  Type your question here...          │        │
│  └──────────────────────────────────────┘        │
│  [ Ask ]                                          │
│                                                   │
│  ℹ️ Answer:                                       │
│  Based on the bank statement, the ending          │
│  balance is $12,345.67.                           │
│                                                   │
│  ▶ View Sources (3 chunks)                        │
│    Source 1 (distance: 0.1234)                    │
│    Document: abc-123, Chunk: 3                    │
│    "Ending Balance: $12,345.67..."                │
└──────────────────────────────────────────────────┘
```

#### Risk Flags Logic

| Document Type | Condition | Flag |
|---------------|-----------|------|
| Loan Application | DTI > 43% | High debt-to-income ratio |
| Pay Stub | Tax rate < 5% or > 50% | Unusual tax withholding |
| Bank Statement | Withdrawals > Deposits | Negative cash flow |

#### Polling Mechanism

After upload, the UI polls `GET /documents/{id}` every 2 seconds for up to 60 seconds (30 retries) until the document status changes to `completed` or `failed`.

---

## 6. Data Flow Diagrams

### 6.1 Document Processing — End-to-End Sequence

```
Client            Gateway           Ingestion         Extraction        Database
  │                  │                  │                  │                │
  │ POST /documents  │                  │                  │                │
  │ (PDF file)       │                  │                  │                │
  │─────────────────>│                  │                  │                │
  │                  │ POST /ingest     │                  │                │
  │                  │ (proxy file)     │                  │                │
  │                  │─────────────────>│                  │                │
  │                  │                  │                  │                │
  │                  │                  │ Save PDF to disk │                │
  │                  │                  │                  │                │
  │                  │                  │ INSERT documents │                │
  │                  │                  │ status=pending   │                │
  │                  │                  │─────────────────────────────────>│
  │                  │                  │                  │                │
  │                  │  {document_id,   │                  │                │
  │  {document_id,   │   status:pending}│                  │                │
  │   status:pending}│<─────────────────│                  │                │
  │<─────────────────│                  │                  │                │
  │                  │                  │                  │                │
  │                  │            [Background Task]        │                │
  │                  │                  │                  │                │
  │                  │                  │ pdf2image → OCR  │                │
  │                  │                  │ (15-30s first    │                │
  │                  │                  │  time, 3-8s/page │                │
  │                  │                  │  after)          │                │
  │                  │                  │                  │                │
  │                  │                  │ UPDATE documents │                │
  │                  │                  │ raw_text, type,  │                │
  │                  │                  │ status=processing│                │
  │                  │                  │─────────────────────────────────>│
  │                  │                  │                  │                │
  │                  │                  │ POST /extract    │                │
  │                  │                  │ {document_id}    │                │
  │                  │                  │─────────────────>│                │
  │                  │                  │                  │                │
  │                  │                  │                  │ SELECT raw_text│
  │                  │                  │                  │───────────────>│
  │                  │                  │                  │<───────────────│
  │                  │                  │                  │                │
  │                  │                  │                  │ Claude API     │
  │                  │                  │                  │ (extraction)   │
  │                  │                  │                  │                │
  │                  │                  │                  │ OpenAI API     │
  │                  │                  │                  │ (embeddings)   │
  │                  │                  │                  │                │
  │                  │                  │                  │ INSERT         │
  │                  │                  │                  │ extractions    │
  │                  │                  │                  │───────────────>│
  │                  │                  │                  │                │
  │                  │                  │                  │ INSERT chunks  │
  │                  │                  │                  │ (with vectors) │
  │                  │                  │                  │───────────────>│
  │                  │                  │                  │                │
  │                  │                  │                  │ UPDATE docs    │
  │                  │                  │                  │ status=done    │
  │                  │                  │                  │───────────────>│
  │                  │                  │                  │                │
  │ GET /documents/  │                  │                  │                │
  │ {id} (polling)   │                  │                  │                │
  │─────────────────>│                  │                  │                │
  │                  │ SELECT docs JOIN │                  │                │
  │                  │ extractions      │                  │                │
  │                  │─────────────────────────────────────────────────────>│
  │                  │<─────────────────────────────────────────────────────│
  │  {status:        │                  │                  │                │
  │   completed,     │                  │                  │                │
  │   extracted_data}│                  │                  │                │
  │<─────────────────│                  │                  │                │
```

### 6.2 RAG Query — Sequence

```
Client            Gateway           RAG                 OpenAI          Claude           Database
  │                  │                │                    │               │                │
  │ POST /query      │                │                    │               │                │
  │ {query: "..."}   │                │                    │               │                │
  │─────────────────>│                │                    │               │                │
  │                  │ POST /query    │                    │               │                │
  │                  │ (proxy)        │                    │               │                │
  │                  │───────────────>│                    │               │                │
  │                  │                │                    │               │                │
  │                  │                │ Embed query        │               │                │
  │                  │                │───────────────────>│               │                │
  │                  │                │ [1536-dim vector]  │               │                │
  │                  │                │<───────────────────│               │                │
  │                  │                │                    │               │                │
  │                  │                │ Cosine similarity  │               │                │
  │                  │                │ search (top 5)     │               │                │
  │                  │                │──────────────────────────────────────────────────────>│
  │                  │                │ [5 chunks + dist]  │               │                │
  │                  │                │<──────────────────────────────────────────────────────│
  │                  │                │                    │               │                │
  │                  │                │ Synthesize answer  │               │                │
  │                  │                │───────────────────────────────────>│                │
  │                  │                │ [answer text]      │               │                │
  │                  │                │<───────────────────────────────────│                │
  │                  │                │                    │               │                │
  │                  │ {answer,       │                    │               │                │
  │  {answer,        │  sources}      │                    │               │                │
  │   sources}       │<───────────────│                    │               │                │
  │<─────────────────│                │                    │               │                │
```

---

## 7. API Reference

All endpoints return the standard envelope format:

```json
{
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "uuid-string",
    "timestamp": "2026-04-01T12:00:00Z"
  }
}
```

On error: `"data": null`, `"error": { "code": "string", "message": "string" }`.

### GET /healthz

**Auth:** No
**Description:** Check health of gateway, database, and downstream services.

**Response (200):**
```json
{
  "status": "ok",
  "db": "up",
  "ingestion": "up",
  "rag": "up"
}
```

**Response (503):** Same shape with `"status": "error"` and degraded service marked `"down"`.

---

### GET /documents

**Auth:** Yes (`Authorization: Bearer <API_KEY>`)
**Description:** List the most recent 50 documents.

**Response (200):**
```json
{
  "data": [
    {
      "id": "a1b2c3d4-...",
      "filename": "bank_statement.pdf",
      "status": "completed",
      "document_type": "bank_statement",
      "page_count": 3,
      "uploaded_at": "2026-04-01T10:00:00Z"
    }
  ],
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### GET /documents/{id}

**Auth:** Yes
**Description:** Get a single document with its extraction results.

**Response (200):**
```json
{
  "data": {
    "id": "a1b2c3d4-...",
    "filename": "bank_statement.pdf",
    "status": "completed",
    "document_type": "bank_statement",
    "page_count": 3,
    "uploaded_at": "2026-04-01T10:00:00Z",
    "extracted_data": {
      "account_number": "1234-5678",
      "account_holder_name": "John Smith",
      "ending_balance": 12345.67,
      "total_deposits": 8500.00,
      "total_withdrawals": 3200.00,
      "statement_date": "March 2026",
      "derived_fields": {
        "total_deposits_snapshot": 8500.00,
        "dti": null
      }
    }
  },
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

**Response (404):** Document not found.

---

### POST /documents

**Auth:** Yes
**Content-Type:** `multipart/form-data`
**Description:** Upload a PDF document for processing.

**Request:**
```
file: <binary PDF>
```

**Response (200):**
```json
{
  "data": {
    "document_id": "a1b2c3d4-...",
    "status": "pending"
  },
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

### POST /query

**Auth:** Yes
**Content-Type:** `application/json`
**Description:** Ask a natural language question over indexed documents.

**Request:**
```json
{
  "query": "What is the ending balance?"
}
```

**Response (200):**
```json
{
  "data": {
    "answer": "Based on the bank statement, the ending balance is $12,345.67.",
    "sources": [
      {
        "id": "chunk-uuid-...",
        "document_id": "a1b2c3d4-...",
        "chunk_index": 3,
        "content": "Ending Balance: $12,345.67\nPrevious Balance: $7,045.67",
        "distance": 0.1234
      }
    ]
  },
  "error": null,
  "meta": { "request_id": "...", "timestamp": "..." }
}
```

---

## 8. Database Schema Reference

### Extensions

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Enums

```sql
CREATE TYPE document_type AS ENUM ('bank_statement', 'loan_application', 'pay_stub');
CREATE TYPE document_status AS ENUM ('pending', 'processing', 'completed', 'failed');
```

### Tables

#### documents

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    document_type document_type,
    status document_status DEFAULT 'pending',
    file_path TEXT,
    raw_text TEXT,
    page_count INTEGER,
    uploaded_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### extractions

```sql
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    extracted_data JSONB,
    confidence_scores JSONB,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

#### chunks

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(document_id, chunk_index)
);
```

### Indexes

```sql
CREATE INDEX idx_chunks_embedding ON chunks
    USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_extractions_data ON extractions
    USING gin (extracted_data);

CREATE INDEX idx_documents_status ON documents (status);
CREATE INDEX idx_documents_type ON documents (document_type);
CREATE INDEX idx_extractions_doc ON extractions (document_id);
CREATE INDEX idx_chunks_doc ON chunks (document_id);
```

### Trigger

```sql
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_modtime
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();
```

---

## 9. Configuration Reference

| Variable | Default | Required | Used By | Description |
|----------|---------|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://findociq:findociq@db:5432/findociq` | No | Gateway, Ingestion, Extraction, RAG | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | *(empty)* | **Yes** | Extraction, RAG | Claude API key for extraction and synthesis |
| `OPENAI_API_KEY` | *(empty)* | **Yes** | Extraction, RAG | OpenAI API key for embeddings |
| `GATEWAY_PORT` | `8080` | No | Gateway | HTTP port for the Go API gateway |
| `INGESTION_PORT` | `8001` | No | Ingestion | HTTP port for the ingestion service |
| `EXTRACTION_PORT` | `8002` | No | Extraction | HTTP port for the extraction service |
| `RAG_PORT` | `8003` | No | RAG | HTTP port for the RAG service |
| `LOG_LEVEL` | `debug` | No | All services | Logging verbosity level |
| `UPLOAD_DIR` | `/data/uploads` | No | Ingestion | Container path for uploaded PDF storage |
| `EXTRACTION_MODEL` | `claude-opus-4-6` | No | Extraction | Claude model for structured extraction |
| `API_KEY` | `changeme` | Recommended | Gateway, UI | Bearer token for API authentication |

**Internal service URLs** (hardcoded defaults, not in `.env`):

| Variable | Default | Used By |
|----------|---------|---------|
| `INGESTION_URL` | `http://ingestion:8001` | Gateway |
| `RAG_URL` | `http://rag:8003` | Gateway |
| `EXTRACTION_SERVICE_URL` | `http://extraction:8002` | Ingestion |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Extraction, RAG |
| `RAG_MODEL` | `claude-opus-4-6` | RAG |
| `API_URL` | `http://gateway:8080` | UI |

---

## 10. Development Workflow

### Makefile Commands

| Command | What It Does |
|---------|-------------|
| `make up` | Start all services in detached mode (`docker compose up -d`) |
| `make down` | Stop all services |
| `make build` | Rebuild all Docker images |
| `make logs` | Stream logs from all services (`docker compose logs -f`) |
| `make clean` | Stop services, remove volumes, delete uploads (full reset) |
| `make test` | Run all tests (Go + Python) |
| `make test-go` | Run Go unit tests (`cd gateway && go test ./...`) |
| `make test-py` | Run Python tests (`pytest services/ tests/ -v`) |
| `make test-e2e` | Run integration tests (`pytest tests/integration/ -v`) |
| `make migrate` | Run Alembic migrations inside extraction container |
| `make lint` | Lint Go (`go vet`) and Python (`ruff check`) code |

### Viewing Logs for a Specific Service

```bash
docker compose logs -f gateway       # Go gateway logs
docker compose logs -f ingestion     # OCR/ingestion logs
docker compose logs -f extraction    # Extraction + embedding logs
docker compose logs -f rag           # RAG query logs
docker compose logs -f ui            # Streamlit logs
docker compose logs -f db            # PostgreSQL logs
```

### Adding a New Document Type

1. Add the type to the `document_type` enum in `db/init.sql` (and create an Alembic migration)
2. Add a Pydantic schema in `services/extraction/app/main.py` (follow existing `BankStatementExtraction` pattern)
3. Add the extraction branch in `process_extraction()` with a type-specific Claude prompt
4. Update the type detection heuristic in `services/ingestion/app/main.py`
5. Add risk flag logic in `ui/app.py` if applicable
6. Add a test fixture PDF in `tests/fixtures/`

### Database Access via Adminer

1. Open http://localhost:8081
2. Login with:
   - System: PostgreSQL
   - Server: `db`
   - Username: `findociq`
   - Password: `findociq`
   - Database: `findociq`
3. Browse tables: `documents`, `extractions`, `chunks`

---

## 11. Troubleshooting

### PaddleOCR Cold Start (15-30 seconds)

The first PDF upload after container start is slow because PaddleOCR loads its ML model into memory. Subsequent uploads process at 3-8 seconds per page.

**Mitigation:** This is expected behavior. The UI shows a "processing" status during this time.

### Extraction Failed

**Symptom:** Document status stuck at `failed`.

**Check:**
```bash
docker compose logs extraction | tail -50
```

**Common causes:**
- `ANTHROPIC_API_KEY` not set or invalid → Claude API returns 401
- `OPENAI_API_KEY` not set or invalid → Embedding generation fails
- Insufficient API credits on either account

### RAG Returns Empty or "I Don't Know"

**Check:** Ensure the document status is `completed` (not just `processing`).
**Check:** Verify chunks exist:
```sql
SELECT COUNT(*) FROM chunks WHERE document_id = '<your-doc-id>';
```
If 0 chunks, the embedding step failed — check `OPENAI_API_KEY`.

### Port Conflicts

If any port is already in use on your machine:

| Port | Service | Fix |
|------|---------|-----|
| 5432 | PostgreSQL | Stop local Postgres or change port in `docker-compose.yml` |
| 8080 | Gateway | Set `GATEWAY_PORT=8090` in `.env` |
| 8081 | Adminer | Change port mapping in `docker-compose.yml` |
| 8001-8003 | Python services | Change `*_PORT` variables in `.env` |
| 8501 | Streamlit | Change port in `docker-compose.yml` (ui service) |

### Database Connection Issues

**Symptom:** Services fail to start, logs show "connection refused" to database.

**Check:**
```bash
docker compose ps          # Verify db container is running and healthy
docker compose logs db     # Check for PostgreSQL errors
```

**Fix:** Ensure the `db` container shows `(healthy)` status. If not, it may need more time on first startup (creating the database and running `init.sql`).

### Container Build Failures

**Symptom:** `docker compose build` fails.

**Common causes:**
- Insufficient disk space (PaddleOCR image is ~2 GB)
- Network issues downloading pip packages
- Docker Desktop not running

**Fix:**
```bash
docker system prune -f     # Clean up unused images/containers
docker compose build --no-cache   # Force fresh build
```
