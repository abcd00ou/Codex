from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pymongo.database import Database

from app.config import Settings, get_settings
from app.database import get_database
from app.schemas import DocumentRecord
from app.services.llm import analyze_topics_with_agent, enhance_pages_with_parsing_agent
from app.services.pdf_parser import chunk_pages, extract_pdf_pages

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(
    db: Database = Depends(get_database),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, description="Case-insensitive filename/title search."),
) -> dict:
    documents = list(
        db.documents.find(
            {},
            {
                "_id": 0,
                "document_id": 1,
                "filename": 1,
                "metadata.title": 1,
                "metadata.page_count": 1,
                "metadata.uploaded_at": 1,
                "chunk_count": 1,
                "paragraph_count": 1,
                "topic_count": 1,
                "agent": 1,
            },
        ).sort("metadata.uploaded_at", -1)
    )
    if search:
        needle = search.lower().strip()
        documents = [
            document
            for document in documents
            if needle in str(document.get("filename", "")).lower()
            or needle in str(document.get("metadata", {}).get("title", "")).lower()
            or needle in str(document.get("document_id", "")).lower()
        ]

    total = len(documents)
    items = documents[offset : offset + limit]
    return {"total": total, "limit": limit, "offset": offset, "documents": items}


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
    parsing_metadata = {
        "agent_used": "disabled",
        "reason": "PARSING_AGENT_ENABLED is false",
        "pages_attempted": 0,
        "pages_enhanced": 0,
    }
    if settings.parsing_agent_enabled:
        pages, parsing_metadata = enhance_pages_with_parsing_agent(
            pages,
            max_pages=settings.parsing_agent_max_pages,
            max_chars_per_page=settings.parsing_agent_max_chars_per_page,
        )

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
        "paragraph_count": sum(len(chunk.get("paragraphs", [])) for chunk in chunks),
        "topic_count": len(topic_analysis["topics"]),
        "agent": {
            "parsing": parsing_metadata,
            "topics": topic_analysis.get("metadata", {}),
        },
    }

    chunk_records = []
    topic_records = []
    chunk_id_by_index: dict[int, str] = {}

    for topic_index, topic in enumerate(topic_analysis["topics"], start=1):
        topic_id = f"topic_{document_id}_{topic_index:03d}"
        chunk_indexes = topic["chunk_indexes"]
        topic_chunk_ids = []
        topic_paragraphs = []

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
                    "paragraphs": chunk.get("paragraphs", []),
                    "paragraph_count": len(chunk.get("paragraphs", [])),
                    "metadata": {
                        "title": record["metadata"]["title"],
                        "source_filename": file.filename,
                        "topic": topic["topic"],
                    },
                    "created_at": now,
                }
            )
            topic_paragraphs.extend(chunk.get("paragraphs", []))

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
                "paragraphs": topic_paragraphs,
                "paragraph_count": len(topic_paragraphs),
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
