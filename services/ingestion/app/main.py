import os
import uuid
import httpx
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import structlog
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
import shutil
import tempfile

logger = structlog.get_logger()
app = FastAPI(title="FinDocIQ Ingestion Service")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://findociq:findociq@db:5432/findociq")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# OCR Setup
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Extraction service URL
EXTRACTION_SERVICE_URL = os.getenv("EXTRACTION_SERVICE_URL", "http://extraction:8002")

def process_document(document_id: str, file_path: str):
    logger.info("Starting document processing", document_id=document_id)
    try:
        # 1. OCR
        logger.info("Converting PDF to images", document_id=document_id)
        images = convert_from_path(file_path)
        page_count = len(images)

        full_text = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, image in enumerate(images):
                img_path = os.path.join(temp_dir, f"page_{i}.png")
                image.save(img_path, "PNG")
                logger.info("Running OCR", document_id=document_id, page=i+1)
                result = ocr.ocr(img_path, cls=True)
                for line in result:
                    if line:
                        for word_info in line:
                            full_text.append(word_info[1][0])

        raw_text = "\n".join(full_text)

        # 2. Simple document type detection
        doc_type = "bank_statement" # default
        lower_text = raw_text.lower()
        if "pay stub" in lower_text or "earnings" in lower_text:
            doc_type = "pay_stub"
        elif "loan application" in lower_text:
            doc_type = "loan_application"

        # 3. Update database
        logger.info("Updating database", document_id=document_id)
        with SessionLocal() as db:
            db.execute(
                text("UPDATE documents SET status = 'processing', raw_text = :raw_text, document_type = :doc_type, page_count = :page_count WHERE id = :id"),
                {"raw_text": raw_text, "doc_type": doc_type, "page_count": page_count, "id": document_id}
            )
            db.commit()

        # 4. Trigger Extraction
        logger.info("Triggering extraction", document_id=document_id)
        with httpx.Client() as client:
            response = client.post(f"{EXTRACTION_SERVICE_URL}/extract", json={"document_id": document_id}, timeout=60.0)
            response.raise_for_status()

    except Exception as e:
        logger.error("Error processing document", document_id=document_id, error=str(e))
        with SessionLocal() as db:
            db.execute(
                text("UPDATE documents SET status = 'failed' WHERE id = :id"),
                {"id": document_id}
            )
            db.commit()


@app.post("/ingest")
async def ingest_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    doc_id = str(uuid.uuid4())
    upload_dir = "/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{doc_id}.pdf")

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create database record
    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO documents (id, filename, status, file_path) VALUES (:id, :filename, 'pending', :file_path)"),
            {"id": doc_id, "filename": file.filename, "file_path": file_path}
        )
        db.commit()

    # Start processing in background
    background_tasks.add_task(process_document, doc_id, file_path)

    return {"document_id": doc_id, "status": "pending"}

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
