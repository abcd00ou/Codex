from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: str | None = None
    source_filename: str
    page_count: int
    uploaded_at: datetime


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    storage_path: str
    metadata: DocumentMetadata
    chunk_count: int
    topic_count: int = 0


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    page_start: int
    page_end: int
    topic_id: str | None = None
    topic: str | None = None
    topic_summary: str | None = None
    keywords: list[str] = Field(default_factory=list)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopicRecord(BaseModel):
    topic_id: str
    document_id: str
    topic: str
    summary: str
    keywords: list[str] = Field(default_factory=list)
    page_start: int
    page_end: int
    chunk_ids: list[str] = Field(default_factory=list)


class ReportRequest(BaseModel):
    query: str
    limit: int = Field(default=8, ge=1, le=30)


class ReportResponse(BaseModel):
    report_id: str
    query: str
    answer: str
    source_chunks: list[dict[str, Any]]
    created_at: datetime


class DashboardSnapshot(BaseModel):
    snapshot_id: str
    document_count: int
    topic_count: int = 0
    chunk_count: int
    top_documents: list[dict[str, Any]]
    created_at: datetime
