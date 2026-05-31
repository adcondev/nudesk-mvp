import asyncio
import os
import uuid
from datetime import datetime, timezone

import httpx
import shutil
import structlog
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import tempfile

logger = structlog.get_logger()
app = FastAPI(title="FinDocIQ Ingestion Service")

# Database setup — sync engine is fine; process_document runs in asyncio.to_thread
DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "postgresql://findociq:findociq@db:5432/findociq")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# OCR Setup
ocr = PaddleOCR(use_angle_cls=True, lang='en')

EXTRACTION_SERVICE_URL = os.getenv("EXTRACTION_SERVICE_URL", "http://extraction:8002")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/uploads")


def _run_ocr(file_path: str) -> tuple[str, int]:
    """Blocking OCR — run via asyncio.to_thread."""
    images = convert_from_path(file_path)
    page_count = len(images)
    full_text: list[str] = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, image in enumerate(images):
            img_path = os.path.join(temp_dir, f"page_{i}.png")
            image.save(img_path, "PNG")
            result = ocr.ocr(img_path, cls=True)
            for line in result:
                if line:
                    for word_info in line:
                        full_text.append(word_info[1][0])
    return "\n".join(full_text), page_count


async def process_document(document_id: str, file_path: str) -> None:
    log = logger.bind(document_id=document_id)
    log.info("starting document processing")
    try:
        log.info("running ocr")
        raw_text, page_count = await asyncio.to_thread(_run_ocr, file_path)

        # Simple doc type detection — extraction service can refine later
        doc_type = "bank_statement"
        lower_text = raw_text.lower()
        if "pay stub" in lower_text or "earnings statement" in lower_text:
            doc_type = "pay_stub"
        elif "loan application" in lower_text:
            doc_type = "loan_application"

        log.info("updating database", doc_type=doc_type, page_count=page_count)
        with SessionLocal() as db:
            db.execute(
                text(
                    "UPDATE documents SET status = 'processing', raw_text = :raw_text, "
                    "document_type = :doc_type, page_count = :page_count WHERE id = :id"
                ),
                {"raw_text": raw_text, "doc_type": doc_type, "page_count": page_count, "id": document_id},
            )
            db.commit()

        log.info("triggering extraction")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EXTRACTION_SERVICE_URL}/extract",
                json={"document_id": document_id},
                timeout=60.0,
            )
            response.raise_for_status()

    except Exception as e:
        log.error("document processing failed", error=str(e))
        with SessionLocal() as db:
            db.execute(
                text("UPDATE documents SET status = 'failed' WHERE id = :id"),
                {"id": document_id},
            )
            db.commit()


def _envelope(data=None, error=None, request_id: str = "") -> dict:
    return {
        "data": data,
        "error": error,
        "meta": {"request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()},
    }


@app.post("/ingest")
async def ingest_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    doc_id = str(uuid.uuid4())
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO documents (id, filename, status, file_path) VALUES (:id, :filename, 'pending', :file_path)"),
            {"id": doc_id, "filename": file.filename, "file_path": file_path},
        )
        db.commit()

    background_tasks.add_task(process_document, doc_id, file_path)

    return _envelope(data={"document_id": doc_id, "status": "pending"})


@app.get("/healthz")
async def health_check():
    return _envelope(data={"status": "ok"})
