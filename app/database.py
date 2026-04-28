from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

from app.config import get_settings
from app.local_store import LocalDatabase


def get_database() -> Database | LocalDatabase:
    settings = get_settings()
    if settings.mongodb_uri == "local://dev":
        return LocalDatabase(settings.storage_dir / "local_db.json")

    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    db = client[settings.mongodb_db]
    try:
        client.admin.command("ping")
        ensure_indexes(db)
    except ServerSelectionTimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "MongoDB에 연결할 수 없습니다. MONGODB_URI를 확인하거나 "
                "`docker compose up -d mongodb`로 로컬 DB를 실행하세요. "
                "개발용 파일 저장소를 쓰려면 MONGODB_URI=local://dev 로 설정하세요."
            ),
        ) from exc
    return db


def ensure_indexes(db: Database) -> None:
    db.documents.create_index("document_id", unique=True)
    db.document_topics.create_index("document_id")
    db.document_topics.create_index([("topic", "text"), ("summary", "text"), ("keywords", "text")])
    db.document_chunks.create_index("document_id")
    db.document_chunks.create_index(
        [
            ("text", "text"),
            ("topic", "text"),
            ("topic_summary", "text"),
            ("keywords", "text"),
            ("metadata.title", "text"),
        ]
    )
    db.reports.create_index("report_id", unique=True)
    db.dashboard_snapshots.create_index("snapshot_id", unique=True)
