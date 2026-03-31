from fastapi import FastAPI
import structlog

logger = structlog.get_logger()
app = FastAPI(title="FinDocIQ Service")

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
