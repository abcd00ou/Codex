from datetime import datetime
from typing import Any, Literal

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
    paragraph_count: int = 0
    topic_count: int = 0
    agent: dict[str, Any] = Field(default_factory=dict)


class ChunkRecord(BaseModel):
    chunk_id: str
    document_id: str
    page_start: int
    page_end: int
    topic_id: str | None = None
    topic: str | None = None
    topic_summary: str | None = None
    keywords: list[str] = Field(default_factory=list)
    paragraphs: list[dict[str, Any]] = Field(default_factory=list)
    paragraph_count: int = 0
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
    paragraphs: list[dict[str, Any]] = Field(default_factory=list)
    paragraph_count: int = 0


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
    paragraph_count: int = 0
    top_documents: list[dict[str, Any]]
    created_at: datetime


WorkflowStatus = Literal["pending", "running", "needs_input", "succeeded", "failed"]
WorkflowStepStatus = Literal["pending", "running", "succeeded", "failed", "skipped"]
WorkflowStepKind = Literal[
    "llm_plan",
    "llm_extract",
    "llm_summarize",
    "llm_review",
    "internal_search_documents",
    "internal_create_report",
]


class WorkflowRunRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)
    input_data: dict[str, Any] = Field(default_factory=dict)


class WorkflowResumeRequest(BaseModel):
    input_data: dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    step_id: str
    name: str
    kind: WorkflowStepKind
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    status: WorkflowStepStatus = "pending"
    error: str | None = None
    attempts: int = 0


class AgentDecision(BaseModel):
    next_action: str
    reason: str
    step_updates: list[dict[str, Any]] = Field(default_factory=list)
    final_answer: str | None = None


class WorkflowRun(BaseModel):
    run_id: str
    goal: str
    status: WorkflowStatus
    steps: list[WorkflowStep] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    input_data: dict[str, Any] = Field(default_factory=dict)
    questions: list[str] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
