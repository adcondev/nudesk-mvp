import json
import os
import re
from datetime import datetime, timezone
from typing import Optional

import structlog
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

load_dotenv()
logger = structlog.get_logger()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://findociq:findociq@db:5432/findociq")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "claude-opus-4-6")
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

app = FastAPI(title="FinDocIQ Extraction Service")


class BankStatementExtraction(BaseModel):
    account_number: Optional[str] = Field(None, description="Account number from the statement.")
    account_holder_name: Optional[str] = Field(None, description="Name on the account.")

class LoanApplicationExtraction(BaseModel):
    applicant_name: Optional[str] = Field(None, description="Name of the applicant.")
    social_security_number: Optional[str] = Field(None, description="SSN of the applicant.")
    loan_amount: Optional[float] = Field(None, description="Requested loan amount.")
    monthly_gross_income: Optional[float] = Field(None, description="Stated monthly gross income.")
    monthly_debt_payments: Optional[float] = Field(None, description="Stated total monthly debt payments.")
    calculated_dti: Optional[float] = Field(None, description="Calculated Debt-to-Income ratio.")
    statement_date: Optional[str] = Field(None, description="Statement issue date.")
    total_deposits: Optional[float] = Field(None, description="Total deposits/credits for the period.")
    total_withdrawals: Optional[float] = Field(None, description="Total withdrawals/debits for the period.")
    ending_balance: Optional[float] = Field(None, description="Closing balance at end of statement period.")


class ExtractRequest(BaseModel):
    document_id: str


def _parse_claude_json(text: str) -> dict:
    """Extract JSON from Claude response, stripping markdown fences if present."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def _envelope(data=None, error=None, request_id: str = "") -> dict:
    return {
        "data": data,
        "error": error,
        "meta": {"request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()},
    }


async def _embed_and_index_chunks(document_id: str, raw_text: str, log):
    log.info("starting chunking and embedding")
    # Simple paragraph chunking
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

    if not paragraphs:
        log.warning("no paragraphs found to chunk")
        return

    # Call OpenAI for embeddings
    try:
        response = await openai_client.embeddings.create(
            input=paragraphs,
            model=EMBEDDING_MODEL
        )
    except Exception as e:
        log.error("embedding failed", error=str(e))
        return

    # Insert chunks to database
    try:
        async with AsyncSessionLocal() as session:
            for i, data in enumerate(response.data):
                embedding = data.embedding
                content = paragraphs[i]
                await session.execute(
                    text(
                        "INSERT INTO chunks (document_id, chunk_index, content, embedding) "
                        "VALUES (:document_id, :chunk_index, :content, :embedding::vector)"
                    ),
                    {
                        "document_id": document_id,
                        "chunk_index": i,
                        "content": content,
                        "embedding": str(embedding)
                    }
                )
            await session.commit()
            log.info("indexed chunks successfully", chunk_count=len(paragraphs))
    except Exception as e:
        log.error("failed to insert chunks to db", error=str(e))

async def process_extraction(document_id: str) -> None:
    log = logger.bind(document_id=document_id)
    log.info("starting extraction")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT raw_text, document_type FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            row = result.fetchone()
            if not row or not row.raw_text:
                log.error("document or raw text not found")
                return

            raw_text, doc_type = row

            if doc_type == "bank_statement":
                prompt = f"""Extract the requested fields from the following bank statement text.
Return ONLY a JSON object matching this schema — no explanation, no markdown:
{{
    "account_number": "string or null",
    "account_holder_name": "string or null",
    "statement_date": "string or null",
    "total_deposits": number or null,
    "total_withdrawals": number or null,
    "ending_balance": number or null
}}

Document text:
<document>
{raw_text}
</document>"""

                log.info("calling claude api", model=EXTRACTION_MODEL)
                response = await anthropic_client.messages.create(
                    model=EXTRACTION_MODEL,
                    max_tokens=1000,
                    temperature=0,
                    system="You are an expert at extracting structured data from financial documents. Return only JSON.",
                    messages=[{"role": "user", "content": prompt}],
                )

                if not response.content:
                    raise ValueError("empty response from Claude API")

                extracted_data = _parse_claude_json(response.content[0].text)
                validated = BankStatementExtraction(**extracted_data).model_dump()

                # Derived fields — only compute what the data actually supports.
                # A single bank statement snapshot does not provide enough data for a true
                # DTI ratio (which requires verified monthly debt obligations). We expose
                # total_deposits as the best single-statement income proxy and leave dti
                # null until multi-statement or loan application data is available.
                deposits = validated.get("total_deposits")
                validated["derived_fields"] = {
                    "total_deposits_snapshot": deposits,
                    "dti": None,  # requires verified debt payments — not available from statement alone
                }

                log.info("extraction successful")

                # trigger chunking and embedding after extraction
                await _embed_and_index_chunks(document_id, raw_text, log)

                await session.execute(
                    text(
                        "INSERT INTO extractions (document_id, extracted_data, model_version) "
                        "VALUES (:document_id, :extracted_data, :model_version)"
                    ),
                    {
                        "document_id": document_id,
                        "extracted_data": json.dumps(validated),
                        "model_version": EXTRACTION_MODEL,
                    },
                )
                await session.execute(
                    text("UPDATE documents SET status = 'completed' WHERE id = :id"),
                    {"id": document_id},
                )
                await session.commit()

            elif doc_type == "loan_application":
                prompt = f"""Extract the requested fields from the following loan application text.
Return ONLY a JSON object matching this schema — no explanation, no markdown:
{{
    "applicant_name": "string or null",
    "social_security_number": "string or null",
    "loan_amount": number or null,
    "monthly_gross_income": number or null,
    "monthly_debt_payments": number or null,
    "calculated_dti": number or null
}}

Document text:
<document>
{raw_text}
</document>"""

                log.info("calling claude api for loan app", model=EXTRACTION_MODEL)
                response = await anthropic_client.messages.create(
                    model=EXTRACTION_MODEL,
                    max_tokens=1000,
                    temperature=0,
                    system="You are an expert at extracting structured data from financial documents. Return only JSON.",
                    messages=[{"role": "user", "content": prompt}],
                )

                if not response.content:
                    raise ValueError("empty response from Claude API")

                extracted_data = _parse_claude_json(response.content[0].text)
                validated = LoanApplicationExtraction(**extracted_data).model_dump()

                # Derived fields
                income = validated.get("monthly_gross_income")
                debt = validated.get("monthly_debt_payments")
                dti = None
                if income and debt and income > 0:
                    dti = debt / income

                validated["derived_fields"] = {
                    "dti": dti if dti is not None else validated.get("calculated_dti")
                }

                log.info("extraction successful")

                # trigger chunking and embedding after extraction
                await _embed_and_index_chunks(document_id, raw_text, log)

                await session.execute(
                    text(
                        "INSERT INTO extractions (document_id, extracted_data, model_version) "
                        "VALUES (:document_id, :extracted_data, :model_version)"
                    ),
                    {
                        "document_id": document_id,
                        "extracted_data": json.dumps(validated),
                        "model_version": EXTRACTION_MODEL,
                    },
                )
                await session.execute(
                    text("UPDATE documents SET status = 'completed' WHERE id = :id"),
                    {"id": document_id},
                )
                await session.commit()

            else:
                log.warning("unsupported document type — skipping extraction", doc_type=doc_type)
                await session.execute(
                    text("UPDATE documents SET status = 'completed' WHERE id = :id"),
                    {"id": document_id},
                )
                await session.commit()

    except Exception as e:
        log.error("extraction failed", error=str(e))
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE documents SET status = 'failed' WHERE id = :id"),
                {"id": document_id},
            )
            await session.commit()


@app.post("/extract")
async def extract_data(request: ExtractRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_extraction, request.document_id)
    return _envelope(data={"status": "extraction_started", "document_id": request.document_id})


@app.get("/healthz")
async def health_check():
    return _envelope(data={"status": "ok"})
