## Live demo moments for the presentation

Three Claude Code moments to run live during the demo call. Each is self-contained, takes under 60 seconds, and tells a specific part of the story. Run them in this order.

---

### Moment 1 — Scaffold a new doc type (`~30 seconds`)

**Story:** "Adding a new document type is a Claude Code command, not a sprint."

Run:
```
/project:new-doc-type invoice
```

What Claude Code will do:
1. Add `invoice` to the `DocumentType` enum in `services/extraction/app/models/document_types.py`
2. Add the Go constant to `gateway/internal/types/document.go`
3. Create the Pydantic schema at `services/extraction/app/schemas/invoice.py` with fields like `invoice_number`, `vendor_name`, `total_amount`, `due_date`, `line_items`
4. Add the extraction branch in `services/extraction/app/main.py` with a Claude prompt
5. Create a fixture placeholder note and a pytest schema test
6. Update CLAUDE.md domain vocabulary

**Talking point while it runs:** "The extraction prompt, the schema, the test — it's all consistent with the existing patterns because Claude Code reads the conventions from the codebase before writing anything."

---

### Moment 2 — Full pipeline validation (`~60 seconds`)

**Story:** "The system is running. Let me prove it."

Run:
```
/project:test-pipeline bank_statement
```

What Claude Code will do:
1. Hit all four `/healthz` endpoints and report status
2. Upload a fixture PDF from `tests/fixtures/`
3. Poll until extraction completes (status = `completed`)
4. Send a RAG query and verify the answer has sources
5. Print a pass/fail report for each step

**Talking point while it runs:** "Every step in this test is exactly what the analyst does — upload, wait, ask. The difference is this runs in 60 seconds and logs every decision."

---

### Moment 3 — Live code review (`~20 seconds`)

**Story:** "Claude Code isn't just a code generator — it's a quality gate."

Run:
```
/project:review
```

What Claude Code will do:
1. Check for uncommitted changes
2. Validate against architecture rules (Go routing-only, Python async, envelope responses, no hardcoded secrets, logging standards)
3. Surface any error handling gaps, missing type hints, or endpoints without tests
4. Output a structured summary: ✓ Good, ✗ Fix, ~ Consider

**Talking point on the output:** "It flags things like missing test coverage, inconsistent error codes, functions over 50 lines. This runs before every PR in our workflow."

---

### Pre-demo checklist

Before the call, verify:
- [ ] `docker-compose up` — all services healthy at `localhost:8080/healthz`
- [ ] At least one fixture PDF exists in `tests/fixtures/` (bank_statement recommended)
- [ ] Claude Code is open in a terminal with the project directory
- [ ] `API_KEY=changeme` matches `.env` (default works for demo)
- [ ] Loom recording link is ready as backup if the live demo fails
