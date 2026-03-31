from fastapi import FastAPI
from pydantic import BaseModel
import structlog
import os
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger()
app = FastAPI(title="FinDocIQ Service")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://findociq:findociq@db:5432/findociq")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
RAG_MODEL = os.getenv("RAG_MODEL", "claude-opus-4-6")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

def _envelope(data=None, error=None, request_id: str = "") -> dict:
    from datetime import datetime, timezone
    return {
        "data": data,
        "error": error,
        "meta": {"request_id": request_id, "timestamp": datetime.now(timezone.utc).isoformat()},
    }

@app.post("/query")
async def query_rag(request: QueryRequest):
    log = logger.bind(query=request.query)
    log.info("received rag query")

    # embed the query
    try:
        response = await openai_client.embeddings.create(
            input=[request.query],
            model=EMBEDDING_MODEL
        )
        query_embedding = response.data[0].embedding
    except Exception as e:
        log.error("failed to embed query", error=str(e))
        return _envelope(error="Failed to process query")

    # retrieve context
    context_chunks = []
    try:
        async with AsyncSessionLocal() as session:
            # using <=> for cosine distance operator, ordering by distance and limiting to 5
            # returning distance as well
            result = await session.execute(
                text(
                    "SELECT id, document_id, chunk_index, content, embedding <=> :query_embedding::vector AS distance "
                    "FROM chunks "
                    "ORDER BY embedding <=> :query_embedding::vector "
                    "LIMIT 5"
                ),
                {"query_embedding": str(query_embedding)}
            )
            rows = result.fetchall()
            for row in rows:
                context_chunks.append({
                    "id": str(row.id),
                    "document_id": str(row.document_id),
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "distance": float(row.distance)
                })
    except Exception as e:
        log.error("failed to retrieve context", error=str(e))
        return _envelope(error="Failed to retrieve context")

    if not context_chunks:
        return _envelope(data={"answer": "No relevant context found.", "sources": []})

    # synthesize answer
    context_text = "\n\n".join([f"Source {i+1}:\n{chunk['content']}" for i, chunk in enumerate(context_chunks)])
    prompt = f"""You are a helpful assistant answering questions about financial documents.
Use the following context to answer the user's question. If the context does not contain the answer, say "I don't know based on the provided documents."

Context:
<context>
{context_text}
</context>

Question: {request.query}
"""
    try:
        claude_res = await anthropic_client.messages.create(
            model=RAG_MODEL,
            max_tokens=1000,
            temperature=0,
            system="You are an expert financial assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = claude_res.content[0].text
    except Exception as e:
        log.error("failed to synthesize answer", error=str(e))
        return _envelope(error="Failed to generate answer")

    return _envelope(data={"answer": answer, "sources": context_chunks})
