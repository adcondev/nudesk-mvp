# FinDocIQ — Presentation Materials

## Loom Recording Script (3 minutes)

Use this as your shot list. Record in one take with no cuts if possible — it reads as more authentic.

### 0:00–0:30 — The Problem

Open a blank Excel spreadsheet. Narrate:

> "This is what a BPO analyst stares at for six hours every time a new client batch arrives. Bank statements, loan applications, pay stubs — each one manually keyed field by field. Error rate around 12%. No audit trail. No way to ask questions across documents. That's what we're replacing."

### 0:30–1:00 — Upload

Switch to the FinDocIQ UI at `http://localhost:8501`.

- Upload `tests/fixtures/bank_statement.pdf`
- Click **Upload & Process**
- Narrate while the status polling runs:

> "OCR is running now — PaddleOCR, fully local, no data leaving the machine. Once text is extracted, Claude parses structured fields from it."

### 1:00–1:30 — Extraction Results

Extraction completes. Walk through the results panel:

> "Account holder, account number, statement date, total deposits, total withdrawals, ending balance — all extracted in about 30 seconds. No template. No regex. Claude reads it like a person would, but consistently."

Point to the risk flags panel:

> "No red flags on this one. Upload a loan application and you'd see the DTI ratio calculated automatically, highlighted red if it exceeds the 43% standard threshold."

### 1:30–2:00 — RAG Query

Type in the query box:

> "What is the account holder's total deposits for the period?"

Click **Ask**. Show the answer and expand **View Sources**:

> "The answer is grounded. Every claim links back to the exact text chunk it came from — full audit trail. You can ask anything across all indexed documents."

### 2:00–2:30 — Claude Code Live

Switch to the terminal with Claude Code open. Run:

```
/project:new-doc-type invoice
```

Narrate while it runs:

> "The system is designed to extend. I'm asking Claude Code to scaffold a new document type — invoice — right now. It's writing the Pydantic schema, the Claude extraction prompt, the test, updating the domain model. Done in under a minute."

### 2:30–3:00 — Close

Switch back to the spreadsheet.

> "Six hours to 30 seconds. Structured data, sourced answers, extensible to any document type. This is the baseline — we can onboard your pilot batch next week."

---

## 5-Minute Presentation Narrative

### Minute 1 — The Problem

"BPO firms process thousands of financial documents every month. Each analyst spends 4–6 hours per document batch manually entering data from bank statements, loan applications, pay stubs. Industry error rate hovers around 10–12%. There's no cross-document querying — if a client asks 'what was the average monthly deposit across all six of this borrower's statements,' someone has to manually read six PDFs and compute it. We think this is an obvious AI problem that nobody has packaged cleanly for BPO workflows."

### Minute 2 — The Solution

"FinDocIQ is a document intelligence pipeline built specifically for BPO intake. You upload a PDF. PaddleOCR extracts the text locally — no data leaves the machine. Claude parses structured fields from the OCR output using prompt-based extraction, which means it generalises across layout variations without templates or regex. The extracted data and raw text are both indexed into pgvector — the same database, no additional services. From there, analysts can ask natural language questions and get sourced answers. Every response traces back to the exact text it came from."

### Minute 3–4 — Live Demo

_(Run the live demo from the Loom script steps above, or play the Loom recording as backup.)_

Key moments to call out:
- The status polling: "This would be a WebSocket in production — we're using polling for the MVP."
- The risk flags panel: "These thresholds are configurable — 43% DTI is the standard but you'd tune this per client."
- The View Sources expander: "This is the audit trail. Compliance teams love this."
- The `/new-doc-type invoice` demo: "Adding a new document type is a Claude Code command, not a sprint."

### Minute 5 — Roadmap + Ask

"What you've seen is the MVP — three document types, local stack, single user. The production roadmap from here is clear:

1. **Multi-document reasoning** — cross-reference income across six bank statements in one query
2. **n8n orchestration** — replace the synchronous HTTP pipeline with a proper workflow engine
3. **PII redaction layer** — before OCR text hits the database, strip names, SSNs, account numbers
4. **React frontend** — Streamlit is a demo surface; the production UI is a React app with role-based views per analyst tier
5. **Production auth** — OAuth2 + RBAC per client tenant

The question is which of your document types we tackle first. We can have a pilot running against your intake batch in two weeks. What does your highest-volume document type look like?"

---

## Backup Plan (If Live Demo Breaks)

1. Play the Loom recording
2. Walk through the architecture diagram from the README
3. Show the Claude Code commands in `.claude/commands/` — the code tells the story even without a running stack
4. Offer to run a live demo after the call once the environment is restored
