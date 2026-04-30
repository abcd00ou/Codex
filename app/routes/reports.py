from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.database import get_database
from app.schemas import ReportRequest, ReportResponse
from app.services.llm import summarize_with_llm

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
def list_reports(
    db: Database = Depends(get_database),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, description="Case-insensitive query/answer search."),
) -> dict:
    reports = list(
        db.reports.find(
            {},
            {
                "_id": 0,
                "report_id": 1,
                "query": 1,
                "answer": 1,
                "source_chunks": 1,
                "created_at": 1,
            },
        ).sort("created_at", -1)
    )
    if search:
        needle = search.lower().strip()
        reports = [
            report
            for report in reports
            if needle in str(report.get("query", "")).lower()
            or needle in str(report.get("answer", "")).lower()
            or needle in str(report.get("report_id", "")).lower()
        ]

    total = len(reports)
    items = reports[offset : offset + limit]
    return {"total": total, "limit": limit, "offset": offset, "reports": items}


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
