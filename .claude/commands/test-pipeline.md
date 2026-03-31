## End-to-end pipeline test
 
Run a full pipeline test against the running docker-compose stack.
 
### Step 1 — Health checks
```
curl -sf localhost:8080/healthz   # gateway
curl -sf localhost:8001/healthz   # ingestion
curl -sf localhost:8002/healthz   # extraction
curl -sf localhost:8003/healthz   # rag
```
If any service is down, report which ones failed and stop.
 
### Step 2 — Upload a test document
Find a PDF in `tests/fixtures/`. Upload it:
```
curl -X POST localhost:8080/api/v1/documents -F "file=@<fixture_path>"
```
Verify: 200 response, document ID in envelope format.
 
### Step 3 — Check extraction
Poll `GET localhost:8080/api/v1/documents/<id>` every 2 seconds until status is `extracted` or 30s timeout. Verify extraction fields are populated.
 
### Step 4 — Test RAG query
```
curl -X POST localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total amount on this document?"}'
```
Verify: response contains answer text and at least one citation.
 
### Step 5 — Report
Print pass/fail for each step. If `$ARGUMENTS` contains "verbose", include full response bodies.
