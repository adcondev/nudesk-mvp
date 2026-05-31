## Add a new financial document type

Scaffold a complete new document type "$ARGUMENTS" across the full stack. This command demonstrates FinDocIQ's extensibility — a new doc type goes from zero to testable in one command.

### What you'll create

1. **Python enum** — add `$ARGUMENTS` to `DocumentType` in `services/extraction/app/models/document_types.py`

2. **Go constant** — add the matching constant to `gateway/internal/types/document.go`

3. **Pydantic schema** — create `services/extraction/app/schemas/$ARGUMENTS.py`
   - Define a Pydantic v2 model (use `Optional[str]` / `Optional[float]` fields, all nullable)
   - Include a `derived_fields` dict for any computed values (ratios, totals)
   - Study `services/extraction/app/main.py` for the pattern used by `BankStatementExtraction`, `LoanApplicationExtraction`, `PayStubExtraction`

4. **Claude extraction prompt** — add a new `elif doc_type == "$ARGUMENTS":` branch in `process_extraction()` in `services/extraction/app/main.py`
   - Follow the exact same pattern as existing branches: build prompt → call Claude API → `_parse_claude_json` → validate with Pydantic → compute derived fields → `_embed_and_index_chunks` → INSERT into extractions → UPDATE status to completed

5. **Alembic migration** — only if new DB columns are required (most doc types use the existing JSONB `extracted_data` column and need no migration)

6. **Test fixture note** — create `tests/fixtures/$ARGUMENTS_sample.md` describing what a synthetic sample document should contain (fields, format, realistic but fake values)

7. **Pytest schema test** — create `services/extraction/tests/test_$ARGUMENTS.py`
   - Instantiate the Pydantic model with a dict of realistic values
   - Assert all expected fields are present
   - Assert derived field computation is correct (e.g., ratio = a/b)
   - Follow the pattern in any existing test files

8. **CLAUDE.md update** — add `$ARGUMENTS` to the `document_type` enum list in the Domain vocabulary section

### Conventions to follow
- Keep the schema minimal — only fields present on *most* documents of this type
- All schema fields are `Optional` — extraction may miss fields on unusual layouts
- Derived fields go in a nested `derived_fields` dict, not as top-level fields
- Log at each stage: `log.info("calling claude api", model=EXTRACTION_MODEL)`, `log.info("extraction successful")`
- Never hardcode model names — always use `EXTRACTION_MODEL` env var
