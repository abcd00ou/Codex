from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database import get_database
from app.schemas import ReportRequest, ReportResponse
from app.services.llm import summarize_with_llm

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
def create_report(
    request: ReportRequest,
    db: Database = Depends(get_database),
) -> ReportResponse:
    chunks = list(
        db.document_chunks.find(
            {"$text": {"$search": request.query}},
            {
                "_id": 0,
                "chunk_id": 1,
                "document_id": 1,
                "page_start": 1,
                "page_end": 1,
                "topic_id": 1,
                "topic": 1,
                "topic_summary": 1,
                "keywords": 1,
                "text": 1,
                "metadata": 1,
                "score": {"$meta": "textScore"},
            },
        )
        .sort([("score", {"$meta": "textScore"})])
        .limit(request.limit)
    )

    if not chunks:
        chunks = list(
            db.document_chunks.find(
                {},
                {
                    "_id": 0,
                    "chunk_id": 1,
                    "document_id": 1,
                    "page_start": 1,
                    "page_end": 1,
                    "topic_id": 1,
                    "topic": 1,
                    "topic_summary": 1,
                    "keywords": 1,
                    "text": 1,
                    "metadata": 1,
                },
            ).limit(request.limit)
        )

    answer = summarize_with_llm(request.query, chunks)
    now = datetime.now(UTC)
    report = {
        "report_id": f"report_{uuid4().hex}",
        "query": request.query,
        "answer": answer,
        "source_chunks": [
            {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "topic_id": chunk.get("topic_id"),
                "topic": chunk.get("topic"),
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "keywords": chunk.get("keywords", []),
                "metadata": chunk.get("metadata", {}),
            }
            for chunk in chunks
        ],
        "created_at": now,
    }
    db.reports.insert_one(report)
    return ReportResponse(**report)
