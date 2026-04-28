from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pymongo.database import Database

from app.config import Settings, get_settings
from app.database import get_database
from app.schemas import DocumentRecord
from app.services.llm import analyze_topics_with_agent
from app.services.pdf_parser import chunk_pages, extract_pdf_pages

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRecord)
async def upload_document(
    file: UploadFile = File(...),
    db: Database = Depends(get_database),
    settings: Settings = Depends(get_settings),
) -> DocumentRecord:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    document_id = f"doc_{uuid4().hex}"
    storage_path = settings.storage_dir / f"{document_id}.pdf"
    contents = await file.read()
    storage_path.write_bytes(contents)

    try:
        pages = extract_pdf_pages(storage_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"PDF 파싱 실패: {exc}") from exc

    chunks = chunk_pages(
        pages,
        max_chars=settings.max_chunk_chars,
        overlap_chars=settings.chunk_overlap_chars,
    )
    topic_analysis = analyze_topics_with_agent(chunks)

    now = datetime.now(UTC)
    record = {
        "document_id": document_id,
        "filename": file.filename,
        "storage_path": str(Path(storage_path).resolve()),
        "metadata": {
            "title": file.filename.rsplit(".", 1)[0],
            "source_filename": file.filename,
            "page_count": len(pages),
            "uploaded_at": now,
        },
        "chunk_count": len(chunks),
        "topic_count": len(topic_analysis["topics"]),
    }

    chunk_records = []
    topic_records = []
    chunk_id_by_index: dict[int, str] = {}

    for topic_index, topic in enumerate(topic_analysis["topics"], start=1):
        topic_id = f"topic_{document_id}_{topic_index:03d}"
        chunk_indexes = topic["chunk_indexes"]
        topic_chunk_ids = []

        for chunk_index in chunk_indexes:
            chunk = chunks[chunk_index]
            chunk_id = chunk_id_by_index.get(chunk_index) or f"chunk_{uuid4().hex}"
            chunk_id_by_index[chunk_index] = chunk_id
            topic_chunk_ids.append(chunk_id)
            chunk_records.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "topic_id": topic_id,
                    "topic": topic["topic"],
                    "topic_summary": topic["summary"],
                    "keywords": topic["keywords"],
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                    "text": chunk["text"],
                    "metadata": {
                        "title": record["metadata"]["title"],
                        "source_filename": file.filename,
                        "topic": topic["topic"],
                    },
                    "created_at": now,
                }
            )

        page_starts = [chunks[index]["page_start"] for index in chunk_indexes]
        page_ends = [chunks[index]["page_end"] for index in chunk_indexes]
        topic_records.append(
            {
                "topic_id": topic_id,
                "document_id": document_id,
                "topic": topic["topic"],
                "summary": topic["summary"],
                "keywords": topic["keywords"],
                "page_start": min(page_starts),
                "page_end": max(page_ends),
                "chunk_ids": topic_chunk_ids,
                "created_at": now,
            }
        )

    db.documents.insert_one(record)
    if topic_records:
        db.document_topics.insert_many(topic_records)
    if chunk_records:
        db.document_chunks.insert_many(chunk_records)

    return DocumentRecord(**record)


@router.get("/{document_id}")
def get_document(
    document_id: str,
    db: Database = Depends(get_database),
) -> dict:
    document = db.documents.find_one({"document_id": document_id}, {"_id": 0})
    if document is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    chunks = list(
        db.document_chunks.find(
            {"document_id": document_id},
            {
                "_id": 0,
                "text": 0,
            },
        ).sort("page_start", 1)
    )
    topics = list(
        db.document_topics.find(
            {"document_id": document_id},
            {"_id": 0},
        ).sort("page_start", 1)
    )
    return {"document": document, "topics": topics, "chunks": chunks}


@router.get("/{document_id}/topics")
def get_document_topics(
    document_id: str,
    db: Database = Depends(get_database),
) -> dict:
    document = db.documents.find_one({"document_id": document_id}, {"_id": 0})
    if document is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    topics = list(
        db.document_topics.find(
            {"document_id": document_id},
            {"_id": 0},
        ).sort("page_start", 1)
    )
    return {"document_id": document_id, "topic_count": len(topics), "topics": topics}
