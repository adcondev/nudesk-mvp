## End-to-end pipeline test

Run a full pipeline test against the running docker-compose stack. Validates the complete flow: upload → OCR → extraction → RAG query.

Pass `$ARGUMENTS` as a document type (`bank_statement`, `loan_application`, `pay_stub`) to target a specific fixture. Pass `verbose` to include full response bodies in the report.

### Step 1 — Health checks

Verify all services are reachable:

```bash
curl -sf -H "Authorization: Bearer ${API_KEY:-changeme}" localhost:8080/healthz
curl -sf localhost:8001/healthz
curl -sf localhost:8002/healthz
curl -sf localhost:8003/healthz
```

If any service is down, report which ones failed and stop — do not proceed to upload.

### Step 2 — Upload a test document

Find a PDF in `tests/fixtures/`. If `$ARGUMENTS` specifies a document type, use the matching fixture file. If no fixtures exist, note that and stop with instructions to add one.

```bash
curl -s -X POST localhost:8080/ingest \
  -H "Authorization: Bearer ${API_KEY:-changeme}" \
  -F "file=@<fixture_path>"
```

Verify: HTTP 200, envelope `data.document_id` is a UUID.

### Step 3 — Poll for extraction

Poll `GET /documents/<id>` every 2 seconds until `status == "completed"` or 60s timeout (30 retries):

```bash
curl -s localhost:8080/documents/<id> \
  -H "Authorization: Bearer ${API_KEY:-changeme}"
```

Verify: status is `completed`, `extracted_data` is non-null and contains at least one non-null field.

### Step 4 — RAG query

```bash
curl -s -X POST localhost:8080/query \
  -H "Authorization: Bearer ${API_KEY:-changeme}" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main subject of this document?"}'
```

Verify: HTTP 200, `data.answer` is non-empty, `data.sources` contains at least one entry with `chunk_index` and `content`.

### Step 5 — Report

Print a pass/fail summary for each step:

```
[PASS] Step 1: All services healthy
[PASS] Step 2: Document uploaded (id: <uuid>)
[PASS] Step 3: Extraction completed — fields: account_holder_name, total_deposits, ...
[PASS] Step 4: RAG query returned answer with 3 sources
```

If verbose, include the full JSON response bodies for steps 2–4.
