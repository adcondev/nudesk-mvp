## Add a new financial document type
 
Create a new document type "$ARGUMENTS" by performing these steps:
 
1. Add the type to the DocumentType enum in `services/extraction/app/models/document_types.py`
2. Add the matching Go constant in `gateway/internal/types/document.go`
3. Create a Pydantic extraction schema at `services/extraction/app/schemas/$ARGUMENTS.py` with fields typical for this document type. Study existing schemas for patterns.
4. Create extraction logic at `services/extraction/app/extractors/$ARGUMENTS.py` with the Claude API prompt for this doc type
5. Create an alembic migration if any new DB columns are needed
6. Add a test fixture placeholder note at `tests/fixtures/` (document what sample is needed)
7. Add a pytest test at `services/extraction/tests/test_$ARGUMENTS.py` that validates the schema
8. Update the `domain vocabulary` section in CLAUDE.md — add the new type to the `document_type` enum list
 
Reference existing document types for conventions. Keep the schema minimal — only fields that appear on most documents of this type.
