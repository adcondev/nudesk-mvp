import os
import json
import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from anthropic import AsyncAnthropic
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://findociq:findociq@db:5432/findociq")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Anthropic API setup
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

app = FastAPI(title="FinDocIQ Extraction Service")

# Pydantic models for extraction
class BankStatementExtraction(BaseModel):
    account_number: Optional[str] = Field(description="The account number, typically ending in a few digits.")
    account_holder_name: Optional[str] = Field(description="Name of the person or entity holding the account.")
    statement_date: Optional[str] = Field(description="The date the statement was issued.")
    total_deposits: Optional[float] = Field(description="Total amount of deposits or credits.")
    total_withdrawals: Optional[float] = Field(description="Total amount of withdrawals or debits.")
    ending_balance: Optional[float] = Field(description="The final balance at the end of the statement period.")

class ExtractRequest(BaseModel):
    document_id: str

async def process_extraction(document_id: str):
    logger.info("Starting extraction", document_id=document_id)
    try:
        async with AsyncSessionLocal() as session:
            # Fetch raw text
            result = await session.execute(
                text("SELECT raw_text, document_type FROM documents WHERE id = :id"),
                {"id": document_id}
            )
            row = result.fetchone()
            if not row or not row.raw_text:
                logger.error("Document or raw text not found", document_id=document_id)
                return

            raw_text, doc_type = row

            if doc_type == "bank_statement":
                # Prompt Claude
                prompt = f"""
                You are a data extraction assistant. Extract the requested fields from the following bank statement text.
                Return ONLY a JSON object matching this schema:
                {{
                    "account_number": "string or null",
                    "account_holder_name": "string or null",
                    "statement_date": "string or null",
                    "total_deposits": number or null,
                    "total_withdrawals": number or null,
                    "ending_balance": number or null
                }}

                Here is the document text:
                <document>
                {raw_text}
                </document>
                """

                logger.info("Calling Claude API", document_id=document_id)
                response = await anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0,
                    system="You are an expert at extracting structured data from financial documents. Return only JSON.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                # Parse output
                extracted_json_str = response.content[0].text
                # Find JSON block if Claude included markdown
                if "```json" in extracted_json_str:
                    extracted_json_str = extracted_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in extracted_json_str:
                    extracted_json_str = extracted_json_str.split("```")[1].split("```")[0].strip()

                extracted_data = json.loads(extracted_json_str)
                validated_data = BankStatementExtraction(**extracted_data).model_dump()

                # Derived fields
                deposits = validated_data.get('total_deposits') or 0.0
                withdrawals = validated_data.get('total_withdrawals') or 0.0
                monthly_avg_income = deposits  # Simplification for demo
                # Assume a fixed debt for demo DTI calculation if withdrawals aren't just expenses
                # Or simplify DTI = withdrawals / deposits if deposits > 0
                dti = round(withdrawals / deposits, 2) if deposits > 0 else 0.0

                validated_data["derived_fields"] = {
                    "monthly_avg_income": monthly_avg_income,
                    "dti": dti
                }

                logger.info("Extraction successful", document_id=document_id)

                # Update DB
                await session.execute(
                    text("""
                        INSERT INTO extractions (document_id, extracted_data, model_version)
                        VALUES (:document_id, :extracted_data, :model_version)
                    """),
                    {
                        "document_id": document_id,
                        "extracted_data": json.dumps(validated_data),
                        "model_version": "claude-3-haiku-20240307"
                    }
                )

                await session.execute(
                    text("UPDATE documents SET status = 'completed' WHERE id = :id"),
                    {"id": document_id}
                )
                await session.commit()
            else:
                logger.warning("Unsupported document type for extraction", document_id=document_id, doc_type=doc_type)
                await session.execute(
                    text("UPDATE documents SET status = 'completed' WHERE id = :id"),
                    {"id": document_id}
                )
                await session.commit()

    except Exception as e:
        logger.error("Error during extraction", document_id=document_id, error=str(e))
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE documents SET status = 'failed' WHERE id = :id"),
                {"id": document_id}
            )
            await session.commit()


@app.post("/extract")
async def extract_data(request: ExtractRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_extraction, request.document_id)
    return {"status": "extraction_started", "document_id": request.document_id}

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
