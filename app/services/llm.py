import json
import logging
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

LLM_STATUS: dict[str, Any] = {
    "configured": False,
    "last_call": None,
}


def get_openai_client() -> OpenAI | None:
    settings = get_settings()
    if not settings.openai_api_key:
        LLM_STATUS["configured"] = False
        return None
    kwargs = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    if settings.openai_dep_ticket:
        kwargs["default_headers"] = {"x-dep-ticket": settings.openai_dep_ticket}
    LLM_STATUS["configured"] = True
    return OpenAI(**kwargs)


def get_llm_status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "configured": bool(settings.openai_api_key),
        "model": settings.openai_model,
        "base_url": settings.openai_base_url,
        "has_dep_ticket": bool(settings.openai_dep_ticket),
        "last_call": LLM_STATUS.get("last_call"),
    }


def summarize_with_llm(query: str, chunks: list[dict]) -> str:
    client = get_openai_client()
    context = "\n\n".join(
        f"Source {index + 1} | document={chunk.get('document_id')} | "
        f"topic={chunk.get('topic') or chunk.get('metadata', {}).get('topic')} | "
        f"pages={chunk.get('page_start')}-{chunk.get('page_end')}\n{chunk.get('text', '')}"
        for index, chunk in enumerate(chunks)
    )

    if client is None:
        record_llm_call("report", "fallback", "OPENAI_API_KEY is not configured")
        return fallback_summary(query, chunks)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a reporting agent. Summarize only from the provided "
                "database excerpts. Include concise findings and cite source numbers."
            ),
        },
        {
            "role": "user",
            "content": f"Question: {query}\n\nDatabase excerpts:\n{context}",
        },
    ]
    try:
        return generate_text(client, messages)
    except Exception as exc:
        record_llm_call("report", "fallback", str(exc))
        return fallback_summary(query, chunks)


def fallback_summary(query: str, chunks: list[dict]) -> str:
    if not chunks:
        return "관련 자료를 찾지 못했습니다."

    bullets = []
    for index, chunk in enumerate(chunks[:5], start=1):
        text = " ".join(str(chunk.get("text", "")).split())
        topic = chunk.get("topic") or chunk.get("metadata", {}).get("topic") or "미분류"
        bullets.append(f"{index}. [{topic}] {text[:500]}")

    return (
        "OPENAI_API_KEY가 설정되지 않아 추출형 요약으로 응답합니다.\n\n"
        f"질문: {query}\n\n"
        + "\n".join(bullets)
    )


def analyze_topics_with_agent(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    client = get_openai_client()
    if client is None:
        result = fallback_topic_analysis(chunks)
        result["metadata"] = {
            "agent_used": "fallback",
            "reason": "OPENAI_API_KEY is not configured",
        }
        record_llm_call("topic_extraction", "fallback", "OPENAI_API_KEY is not configured")
        return result

    numbered_chunks = "\n\n".join(
        (
            f"chunk_index={index}\n"
            f"pages={chunk.get('page_start')}-{chunk.get('page_end')}\n"
            f"text={str(chunk.get('text', ''))[:2500]}"
        )
        for index, chunk in enumerate(chunks)
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a document ingestion agent. Split PDF chunks into coherent "
                "subtopics for MongoDB storage. Return only valid JSON with this shape: "
                '{"topics":[{"topic":"string","summary":"string",'
                '"keywords":["string"],"chunk_indexes":[0]}]}. '
                "Every chunk_index must appear exactly once."
            ),
        },
        {
            "role": "user",
            "content": f"Analyze these PDF chunks:\n\n{numbered_chunks}",
        },
    ]

    try:
        response_text = generate_text(client, messages)
        data = _load_json_object(response_text)
        result = normalize_topic_analysis(data, chunks)
        result["metadata"] = {"agent_used": "llm", "reason": None}
        record_llm_call("topic_extraction", "llm", None)
        return result
    except Exception as exc:
        result = fallback_topic_analysis(chunks)
        result["metadata"] = {"agent_used": "fallback", "reason": str(exc)}
        record_llm_call("topic_extraction", "fallback", str(exc))
        return result


def generate_text(client: OpenAI, messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=messages,
        )
        logger.info("LLM call succeeded through Responses API")
        return response.output_text
    except Exception as responses_exc:
        logger.warning("Responses API call failed; trying Chat Completions: %s", responses_exc)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
        )
        logger.info("LLM call succeeded through Chat Completions API")
        return response.choices[0].message.content or ""


def record_llm_call(task: str, mode: str, error: str | None) -> None:
    LLM_STATUS["last_call"] = {
        "task": task,
        "mode": mode,
        "error": error,
        "at": datetime.now(UTC).isoformat(),
    }
    if mode == "llm":
        logger.info("AI task=%s completed with gpt-oss", task)
    else:
        logger.warning("AI task=%s used fallback: %s", task, error)


def normalize_topic_analysis(
    data: dict[str, Any],
    chunks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    topics = []
    seen: set[int] = set()
    chunk_count = len(chunks)

    for raw_topic in data.get("topics", []):
        chunk_indexes = []
        for value in raw_topic.get("chunk_indexes", []):
            if isinstance(value, int) and 0 <= value < chunk_count and value not in seen:
                chunk_indexes.append(value)
                seen.add(value)

        if not chunk_indexes:
            continue

        topic_name = str(raw_topic.get("topic") or "미분류").strip()[:120]
        summary = str(raw_topic.get("summary") or "").strip()[:500]
        keywords = [
            str(keyword).strip()[:40]
            for keyword in raw_topic.get("keywords", [])
            if str(keyword).strip()
        ][:8]
        topics.append(
            {
                "topic": topic_name,
                "summary": summary or _summarize_text(" ".join(chunks[index]["text"] for index in chunk_indexes)),
                "keywords": keywords,
                "chunk_indexes": chunk_indexes,
            }
        )

    for index in range(chunk_count):
        if index not in seen:
            topics.append(_fallback_topic_for_chunk(index, chunks[index]))

    return {"topics": topics}


def fallback_topic_analysis(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    topics_by_name: dict[str, dict[str, Any]] = {}
    for index, chunk in enumerate(chunks):
        topic = _fallback_topic_for_chunk(index, chunk)
        key = topic["topic"]
        if key not in topics_by_name:
            topics_by_name[key] = topic
            continue
        topics_by_name[key]["chunk_indexes"].extend(topic["chunk_indexes"])
        topics_by_name[key]["keywords"] = sorted(
            set(topics_by_name[key]["keywords"]) | set(topic["keywords"])
        )[:8]

    return {"topics": list(topics_by_name.values())}


def _fallback_topic_for_chunk(index: int, chunk: dict[str, Any]) -> dict[str, Any]:
    text = str(chunk.get("text", ""))
    topic = _infer_topic_name(text)
    return {
        "topic": topic,
        "summary": _summarize_text(text),
        "keywords": _extract_keywords(text),
        "chunk_indexes": [index],
    }


def _infer_topic_name(text: str) -> str:
    heading = _first_heading(text)
    if heading:
        return heading

    lowered = text.lower()
    rules = [
        ("재무 및 매출", ["revenue", "sales", "profit", "income", "매출", "수익", "영업이익"]),
        ("리스크 및 이슈", ["risk", "delay", "issue", "리스크", "위험", "지연", "문제"]),
        ("운영 및 공급망", ["supplier", "supply", "operation", "공급", "운영", "생산"]),
        ("대시보드 지표", ["dashboard", "kpi", "metric", "chart", "대시보드", "지표"]),
        ("계약 및 법무", ["contract", "legal", "compliance", "계약", "법무", "규제"]),
    ]
    for name, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return name
    keywords = _extract_keywords(text)
    return " / ".join(keywords[:2]) if keywords else "일반 내용"


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        clean = line.strip(" #\t")
        if not clean or clean.lower().startswith("[page "):
            continue
        if len(clean) <= 80 and (
            clean.isupper()
            or re.match(r"^(\d+[\.\)]|[A-Z][\.\)]|제\s*\d+\s*[장절])\s+", clean)
        ):
            return clean[:80]
    return None


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z가-힣][A-Za-z가-힣0-9_-]{2,}", text.lower())
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "page",
        "document",
        "문서",
        "그리고",
        "또는",
        "대한",
    }
    counts = Counter(word for word in words if word not in stopwords)
    return [word for word, _count in counts.most_common(8)]


def _summarize_text(text: str) -> str:
    normalized = " ".join(text.split())
    return normalized[:300]


def _load_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        text = match.group(0)
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("Expected JSON object")
    return loaded
