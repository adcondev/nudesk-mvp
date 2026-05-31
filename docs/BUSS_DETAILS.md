# FinDocIQ

## Business Details Guide

**Financial Document Intelligence Platform**

Version 1.0 | April 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem: Unstructured Data in Financial BPOs](#2-the-problem-unstructured-data-in-financial-bpos)
3. [The Solution: AI-Augmented Document Operations](#3-the-solution-ai-augmented-document-operations)
4. [What the MVP Does Today](#4-what-the-mvp-does-today)
5. [Business Value Metrics](#5-business-value-metrics)
6. [The Engineering Force Multiplier](#6-the-engineering-force-multiplier)
7. [Strategic Alignment with nuDesk](#7-strategic-alignment-with-nudesk)
8. [Roadmap: From MVP to Enterprise](#8-roadmap-from-mvp-to-enterprise)
9. [Go-to-Market Positioning](#9-go-to-market-positioning)

---

## 1. Executive Summary

FinDocIQ is a working MVP that automates document-heavy workflows for financial services BPOs. Upload a PDF — bank statement, loan application, or pay stub — and the system extracts structured data via OCR and AI, computes risk metrics, flags anomalies, indexes the content for semantic search, and lets analysts query documents in natural language with sourced answers. Built in 48 hours, it converts 15-25 minutes of manual data entry per file into under 30 seconds of automated, verifiable processing.

The core strategic bet: FinDocIQ is not a standalone SaaS product. It is a prototype of an intelligent DeskMate — a specialized digital companion purpose-built for financial services workflows — designed as internal, proprietary infrastructure for AI-native BPOs like nuDesk.

---

## 2. The Problem: Unstructured Data in Financial BPOs

### The Unit Economics of Legacy Operations

In a standard financial BPO or lending environment, a loan operations analyst processes roughly 20 to 30 files per day. Each file requires 15 to 25 minutes of manual data entry, cross-referencing, and verification. That equates to over 6 hours a day of repetitive, error-prone "stare-and-compare" labor that generates zero strategic value.

This manual bottleneck drives real business pain:

- **Slow origination cycles.** The average mortgage process takes 30 to 60 days, driven primarily by manual document verification — not the complexity of the credit decision itself.
- **Application abandonment.** Processing delays cause borrowers to defect to competitors with faster digital experiences, directly destroying revenue.
- **Costly errors.** Human fatigue introduces data entry mistakes that elevate compliance risks and require expensive downstream re-work by senior underwriting staff.

### The Nearshore Wage Pressure

Leading AI-native BPOs utilize nearshore talent (e.g., in Mexico) to maintain time-zone alignment and cultural affinity with U.S. markets. However, technology wages in Mexico have surged 42% over a two-year period, tightening operational margins. The traditional strategy of linearly scaling human headcount to meet demand is no longer financially viable.

FinDocIQ acts as a direct hedge against this wage inflation by shifting the operational model from human-driven data entry to human-in-the-loop AI validation. Analysts elevate from data-entry clerks to strategic financial reviewers.

---

## 3. The Solution: AI-Augmented Document Operations

FinDocIQ replaces manual effort with four interconnected, automated capabilities:

1. **Zero-egress document ingestion.** Analysts upload raw PDFs. Localized OCR (PaddleOCR running on-host, not a cloud API) digitizes the text. No sensitive financial data leaves the network.
2. **Intelligent LLM-driven extraction.** Anthropic's Claude API reads the digitized text and populates rigorous, pre-defined data schemas — extracting fields like employer name, gross pay, ending balance, loan amount, and monthly debt obligations across wildly disparate document formats.
3. **Automated risk flagging.** The system computes derived financial metrics (DTI ratio, LTV ratio, effective tax rate) and flags anomalies against predefined thresholds — instantly triaging clean files from high-risk profiles.
4. **Natural language querying with sources.** Analysts "chat" with documents. Ask "What is the ending balance?" and get a sourced answer citing the exact text chunk it came from, with a cosine distance score for transparency.

This is the DeskMate concept in action: a role-specific AI companion that handles the repetitive work so human specialists focus on complex decision-making.

---

## 4. What the MVP Does Today

The following capabilities are fully implemented and operational in the current codebase. The entire stack runs via a single `docker-compose up --build` command.

### Supported Document Types

| Document Type | Extracted Fields | Derived Metrics |
|---|---|---|
| **Bank Statement** | Account number, holder name, statement date, total deposits, total withdrawals, ending balance | Deposit snapshot (deposits used as income proxy) |
| **Loan Application** | Applicant name, SSN, loan amount, property value, purpose, employment status, credit score, monthly gross income, monthly debt payments | DTI ratio, LTV ratio |
| **Pay Stub** | Employee name, employer name, pay period dates, gross pay, net pay, YTD gross, taxes withheld | Effective tax rate, monthly income proxy |

### Automated Risk Flags

The Streamlit UI evaluates derived metrics against hardcoded thresholds and displays visual alerts:

- **DTI > 43%** — High debt-to-income risk (loan applications)
- **LTV > 80%** — PMI warning (loan applications)
- **Tax rate < 5% or > 50%** — Unusual withholding, investigate (pay stubs)
- **Withdrawals > deposits** — Negative cash flow alert (bank statements)

### RAG Query Engine

Documents are chunked, embedded via OpenAI text-embedding-3-small (1536 dimensions), and indexed into PostgreSQL with pgvector (HNSW index). When an analyst submits a question, the system retrieves the top 5 most relevant chunks via cosine similarity search, synthesizes an answer through the Claude API, and displays the exact source chunks alongside the response for full auditability.

### Architecture Summary

| Service | Technology | Role |
|---|---|---|
| Go API Gateway | Go 1.23, Chi, zerolog | Routing, auth, request IDs, DB reads |
| Ingestion Service | Python, FastAPI, PaddleOCR | OCR, document classification |
| Extraction Service | Python, FastAPI, Claude API, OpenAI | Field extraction, embeddings, indexing |
| RAG Service | Python, FastAPI, Claude API, pgvector | Semantic search, answer synthesis |
| Demo UI | Streamlit | Upload, view extractions, query |
| Database | PostgreSQL 16 + pgvector | Single source of truth |

### Known MVP Constraints

- Single concurrent user (demo-scoped Streamlit interface)
- Synchronous processing pipeline (OCR blocks the worker)
- Polling-based status updates (UI polls every 2 seconds)
- API key authentication only (no OAuth2/RBAC)
- No PII redaction (raw OCR text stored in database)
- No batch processing (one document at a time)

---

## 5. Business Value Metrics

| Metric | Legacy Manual Processing | FinDocIQ | Basis |
|---|---|---|---|
| **Data entry time per file** | 15-25 minutes | < 30 seconds | Measured: OCR (3-8s/page after cold start) + Claude extraction + embedding + indexing |
| **Analyst capacity** | 20-30 files/day | 60-90+ files/day | Derived: 85% time reduction frees analysts to review 3x more files |
| **Extraction accuracy** | Prone to human fatigue errors | High accuracy via deterministic LLM extraction (temperature 0) | Architectural: Claude operates at zero temperature with strict JSON schemas; no benchmarks run on MVP |
| **End-to-end cycle impact** | 30-60 day origination average | Projected 25-75% reduction in document processing component | Industry projection for AI-augmented pipelines; not measured on MVP |

**85% reduction in manual data entry time.** The core metric. Converting 15-25 minutes of human labor per document into under 30 seconds of automated processing.

**3x capacity multiplier.** By removing the data-entry bottleneck, an analyst can oversee 3x more files per day without the BPO incurring linear headcount costs.

**< 30 seconds processing.** From document upload to fully structured extraction, database insertion, and vector indexing for semantic search. Note: PaddleOCR has a one-time cold-start of 15-30 seconds on first call; subsequent pages process at 3-8 seconds each.

---

## 6. The Engineering Force Multiplier

A critical aspect of this MVP is *how* it was built. Orchestrating OCR, vector databases, RAG, a Go API gateway, and a Python microservices backend typically takes an engineering pod weeks or months.

**FinDocIQ was architected and deployed in 48 hours.**

This was achieved by leveraging agentic AI engineering workflows — specifically Anthropic's Claude Code operating with the Model Context Protocol (MCP). During the build:

- A **PostgreSQL MCP server** gave the AI agent live database access to inspect schemas, write migrations, and verify data insertion autonomously.
- A **Bash/Shell MCP server** provided persistent terminal access for running test suites, reading stack traces, and iteratively refactoring code until all tests passed.
- **Custom Skills** encapsulated complex, multi-step procedures (e.g., adding a new document type requires updating Pydantic models, SQL migrations, Go API routes, and tests) into single, repeatable commands — guaranteeing consistency across the codebase.

This proves the force multiplier argument: the technical complexities of AI pipelines are highly manageable. nuDesk can rapidly own its proprietary AI ecosystem rather than relying on expensive, rigid third-party SaaS vendors.

---

## 7. Strategic Alignment with nuDesk

### This is a DeskMate Prototype

nuDesk's DeskMates are described as "intelligent, role-specific digital companions" that "handle repetitive, time-consuming tasks like data entry, lead follow-ups, and reporting." FinDocIQ is exactly that — but for document-heavy workflows in credit operations, KYC, and underwriting.

### Internal Infrastructure, Not a Competing Product

FinDocIQ is positioned as proprietary infrastructure for nuDesk, not a SaaS product competing in the open market. The same architecture serves any role where the bottleneck is unstructured documents: underwriting desks, KYC analysts, compliance reviewers, loan processors.

### Business-First, Not Tech-First

The framing is always ROI: hours saved per analyst, error rates reduced, processing time cut. The technology is the "how," never the headline. This resonates with operators and investors who think in unit economics.

### Extensible by Design

Every component is a future product surface. What the MVP demonstrates today becomes the foundation for multi-tenant SaaS, per-lender fine-tuning, compliance audit trails, and CRM integrations.

---

## 8. Roadmap: From MVP to Enterprise

The following capabilities are **not implemented** in the current MVP. They represent the natural evolution from prototype to production.

| Capability | Description | Business Value |
|---|---|---|
| **Multi-tenancy & per-lender schemas** | Row-level security, per-client extraction configs, isolated RAG indexes | White-label or license as standalone product; new revenue stream |
| **Compliance audit trails** | Log every extraction, query, and decision with timestamps, model versions, confidence scores | Exportable for CFPB/HMDA audits; major enterprise differentiator |
| **CRM & LOS integrations** | Connect to Encompass, Salesforce, HubSpot via workflow automation | Extracted fields auto-populate CRM records; close the loop with existing tools |
| **Fraud & anomaly detection** | ML layer for income inconsistency flags, document tampering, cross-document verification | Catch W-2 vs. bank statement income mismatches automatically |
| **Async processing pipeline** | Job queue (Celery/Redis) replacing synchronous HTTP flow | Handle enterprise volume without timeouts or worker blocking |
| **Production auth** | OAuth2, JWT session management, RBAC | Mandatory for multi-user, multi-tenant deployment |
| **PII redaction** | ML-based detection and masking before database insertion | Regulatory compliance for financial data |
| **Voice-first query interface** | Whisper transcription to RAG to TTS | Hands-free document querying for dual-monitor analysts |
| **On-premise deployment** | Ollama for LLMs, local PaddleOCR, no cloud APIs | Zero data egress for highly regulated clients |

---

## 9. Go-to-Market Positioning

### Talking Points for Executive Stakeholders

**Open with the problem, not the tech.**
"A loan ops analyst at a mid-size lender processes 20-30 files a day. Each file takes 15-25 minutes of manual data entry. That is over 6 hours a day of repetitive, error-prone work. FinDocIQ reduces the data extraction component to under 30 seconds per file."

**Connect to nuDesk's DeskMates explicitly.**
"This is a DeskMate prototype for document-heavy roles. The same architecture serves underwriting desks, KYC analysts, compliance reviewers — any role where the bottleneck is unstructured documents."

**Show the SaaS path.**
"Add multi-tenancy and per-lender fine-tuning, and this becomes a standalone product. The Go API is stateless and horizontally scalable. The data pipeline is schema-agnostic — adding a new document type is a single command."

**The force multiplier closing.**
"I built this end-to-end in 48 hours — OCR, embeddings, RAG, a production API, and a working UI. The technical complexity is solved. What matters at nuDesk is choosing the right problems to solve and moving fast. That is what I am here to do."

### Presentation Flow

| Phase | Time | Focus |
|---|---|---|
| **Business Hook** | 0-5 min | The pain: 6+ hours/day of manual data entry. Position FinDocIQ as the DeskMate that compresses this to minutes. |
| **Live Demo** | 5-20 min | Upload a synthetic PDF. Show extraction, risk flags, RAG query with sources. Then demonstrate Claude Code + MCP building a feature live. |
| **Enterprise Roadmap** | 20-30 min | Transition from MVP constraints to the productization path. Proactively address limitations and map out engineering solutions. |
