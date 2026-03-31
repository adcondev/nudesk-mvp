## Code review against project conventions
 
Review the current changes for quality and architectural compliance.
 
1. Run `git status` to confirm there are changes to review. If clean, report "Nothing to review" and stop.
2. Run `git diff` to see all uncommitted changes (staged + unstaged)
3. Check against architecture rules from CLAUDE.md:
   - Go gateway has NO business logic — only routing, auth, proxying, direct DB reads
   - Python services use `async def` endpoints and Pydantic v2 models
   - All API responses use envelope: `{"data", "error", "meta"}`
   - No service-to-service calls bypassing the gateway (except DB access)
   - Logging uses zerolog (Go) or structlog (Python) — no `fmt.Println` or `print()`
   - No hardcoded credentials, ports, or URLs — everything via env vars
4. Check code quality:
   - Missing error handling on external calls (DB, HTTP, file I/O)
   - Missing type hints on Python function signatures
   - Functions longer than 50 lines (suggest splitting)
   - New endpoints without corresponding tests
5. Output a summary:
   - **Good**: what follows conventions correctly
   - **Fix**: issues that must be addressed (as a checklist)
   - **Consider**: optional improvements
