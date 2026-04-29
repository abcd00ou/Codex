from fastapi import FastAPI

from app.config import get_settings
from app.routes import dashboard, documents, reports
from app.services.llm import get_llm_status

app = FastAPI(
    title="Agentic AI PDF API",
    version="0.1.0",
    description="PDF ingestion, MongoDB storage, reporting, and dashboard agent API.",
)

app.include_router(documents.router, prefix="/v1")
app.include_router(reports.router, prefix="/v1")
app.include_router(dashboard.router, prefix="/v1")


@app.get("/v1")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "agentic-ai-pdf-api",
        "model": settings.openai_model,
        "openai_base_url": settings.openai_base_url,
        "mongodb_db": settings.mongodb_db,
        "storage_backend": "local_json" if settings.mongodb_uri == "local://dev" else "mongodb",
        "ai": get_llm_status(),
    }


@app.get("/v1/ai/status")
def ai_status() -> dict:
    return get_llm_status()
