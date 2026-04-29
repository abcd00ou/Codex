from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database import get_database
from app.schemas import DashboardSnapshot

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.post("/refresh", response_model=DashboardSnapshot)
def refresh_dashboard(db: Database = Depends(get_database)) -> DashboardSnapshot:
    document_count = db.documents.count_documents({})
    topic_count = db.document_topics.count_documents({})
    chunk_count = db.document_chunks.count_documents({})
    paragraph_count = sum(
        chunk.get("paragraph_count", len(chunk.get("paragraphs", [])))
        for chunk in db.document_chunks.find({}, {"_id": 0, "paragraph_count": 1, "paragraphs": 1})
    )
    top_documents = list(
        db.documents.find(
            {},
            {
                "_id": 0,
                "document_id": 1,
                "filename": 1,
                "chunk_count": 1,
                "paragraph_count": 1,
                "topic_count": 1,
                "metadata.page_count": 1,
                "metadata.uploaded_at": 1,
            },
        )
        .sort("metadata.uploaded_at", -1)
        .limit(10)
    )

    snapshot = {
        "snapshot_id": f"dash_{uuid4().hex}",
        "document_count": document_count,
        "topic_count": topic_count,
        "chunk_count": chunk_count,
        "paragraph_count": paragraph_count,
        "top_documents": top_documents,
        "created_at": datetime.now(UTC),
    }
    db.dashboard_snapshots.insert_one(snapshot)
    return DashboardSnapshot(**snapshot)
