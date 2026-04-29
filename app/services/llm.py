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
    provider = get_active_provider()
    if not provider["api_key"]:
        LLM_STATUS["configured"] = False
        return None
    kwargs = {"api_key": provider["api_key"]}
    if provider["base_url"]:
        kwargs["base_url"] = provider["base_url"]
    if provider["dep_ticket"]:
        kwargs["default_headers"] = {"x-dep-ticket": provider["dep_ticket"]}
    LLM_STATUS["configured"] = True
    return OpenAI(**kwargs)


def get_active_provider() -> dict[str, str | None]:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider == "openai":
        return {
            "provider": "openai",
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
            "model": settings.openai_model,
            "dep_ticket": settings.openai_dep_ticket,
        }
    if provider in {"xai", "xai-grok", "grok"}:
        return {
            "provider": "xai",
            "api_key": settings.xai_api_key,
            "base_url": settings.xai_base_url,
            "model": settings.xai_model,
            "dep_ticket": None,
        }
    return {
        "provider": "groq",
        "api_key": settings.groq_api_key,
        "base_url": settings.groq_base_url,
        "model": settings.groq_model,
        "dep_ticket": None,
    }


def get_llm_status() -> dict[str, Any]:
    provider = get_active_provider()
    return {
        "configured": bool(provider["api_key"]),
        "provider": provider["provider"],
        "model": provider["model"],
        "base_url": provider["base_url"],
        "has_dep_ticket": bool(provider["dep_ticket"]),
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
        record_llm_call("report", "fallback", "LLM provider API key is not configured")
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
        "LLM provider API key가 설정되지 않아 추출형 요약으로 응답합니다.\n\n"
        f"질문: {query}\n\n"
        + "\n".join(bullets)
    )


def enhance_pages_with_parsing_agent(
    pages: list[dict[str, Any]],
    max_pages: int,
    max_chars_per_page: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    client = get_openai_client()
    if client is None:
        reason = "LLM provider API key is not configured"
        record_llm_call("pdf_parsing", "fallback", reason)
        return pages, {
            "agent_used": "fallback",
            "reason": reason,
            "pages_attempted": 0,
            "pages_enhanced": 0,
        }

    enhanced_pages = []
    pages_attempted = 0
    pages_enhanced = 0
    errors = []

    for page in pages:
        page_number = int(page.get("page", 0))
        if page_number > max_pages:
            enhanced_pages.append(page)
            continue

        paragraphs = page.get("paragraphs") or []
        raw_text = "\n".join(str(paragraph.get("text", "")) for paragraph in paragraphs).strip()
        if not raw_text:
            enhanced_pages.append(page)
            continue

        pages_attempted += 1
        try:
            enhanced = parse_page_with_agent(client, page, max_chars_per_page)
            quality = evaluate_parsed_page(enhanced, page)
            if quality["score"] >= 0.55:
                enhanced_pages.append(enhanced)
                pages_enhanced += 1
            else:
                enhanced_pages.append(page)
                errors.append(f"page {page_number}: low parsing score {quality['score']}")
        except Exception as exc:
            enhanced_pages.append(page)
            errors.append(f"page {page_number}: {exc}")

    for page in pages[len(enhanced_pages) :]:
        enhanced_pages.append(page)

    mode = "llm" if pages_enhanced else "fallback"
    reason = None if pages_enhanced else "; ".join(errors[:3]) or "No pages were enhanced"
    record_llm_call("pdf_parsing", mode, reason)
    return enhanced_pages, {
        "agent_used": mode,
        "reason": reason,
        "pages_attempted": pages_attempted,
        "pages_enhanced": pages_enhanced,
        "errors": errors[:10],
    }


def parse_page_with_agent(
    client: OpenAI,
    page: dict[str, Any],
    max_chars_per_page: int,
) -> dict[str, Any]:
    page_number = int(page.get("page", 0))
    source_paragraphs = page.get("paragraphs") or []
    raw_blocks = "\n\n".join(
        f"source_id={paragraph.get('paragraph_id')}\ntext={paragraph.get('text')}"
        for paragraph in source_paragraphs
    )[:max_chars_per_page]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a PDF parsing agent. Reconstruct readable paragraphs from extracted PDF text blocks. "
                "Fix broken line wraps and hyphenation. Keep the original language. Do not summarize. "
                "Do not invent content. Return only valid JSON with this shape: "
                '{"paragraphs":[{"text":"string","kind":"heading|paragraph|list|table|footer",'
                '"source_ids":["p1_1"]}]}. '
                "Merge blocks only when they are clearly one paragraph. Remove repeated headers/footers only "
                "when they do not contain document content."
            ),
        },
        {
            "role": "user",
            "content": f"Page {page_number} extracted blocks:\n\n{raw_blocks}",
        },
    ]
    response_text = generate_text(client, messages)
    data = _load_json_object(response_text)
    paragraphs = normalize_parsed_paragraphs(data, page_number, source_paragraphs)
    text = "\n\n".join(paragraph["text"] for paragraph in paragraphs).strip()
    return {
        **page,
        "text": text,
        "paragraphs": paragraphs,
        "parser": {
            "agent_used": "llm",
            "source_paragraph_count": len(source_paragraphs),
            "paragraph_count": len(paragraphs),
        },
    }


def normalize_parsed_paragraphs(
    data: dict[str, Any],
    page_number: int,
    source_paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_text = "\n".join(str(paragraph.get("text", "")) for paragraph in source_paragraphs)
    paragraphs = []
    paragraph_index = 1

    for raw in data.get("paragraphs", []):
        text = " ".join(str(raw.get("text", "")).split()).strip()
        if not text or not parsed_text_is_grounded(text, source_text):
            continue
        kind = str(raw.get("kind") or "paragraph").strip().lower()
        if kind not in {"heading", "paragraph", "list", "table", "footer"}:
            kind = "paragraph"
        source_ids = [
            str(source_id).strip()
            for source_id in raw.get("source_ids", [])
            if str(source_id).strip()
        ][:20]
        paragraphs.append(
            {
                "paragraph_id": f"p{page_number}_{paragraph_index}",
                "page": page_number,
                "paragraph_index": paragraph_index,
                "kind": kind,
                "source_ids": source_ids,
                "text": text,
            }
        )
        paragraph_index += 1

    return paragraphs or source_paragraphs


def evaluate_parsed_page(
    enhanced_page: dict[str, Any],
    source_page: dict[str, Any],
) -> dict[str, Any]:
    enhanced_text = " ".join(str(enhanced_page.get("text", "")).split())
    source_text = " ".join(str(source_page.get("text", "")).split())
    if not source_text:
        return {"score": 0.0, "text_ratio": 0.0, "paragraph_count": 0}

    text_ratio = min(len(enhanced_text) / len(source_text), 1.0)
    source_terms = set(_extract_keywords(source_text)[:30])
    enhanced_terms = set(_extract_keywords(enhanced_text)[:30])
    term_ratio = len(source_terms & enhanced_terms) / len(source_terms) if source_terms else 1.0
    paragraph_count = len(enhanced_page.get("paragraphs") or [])
    paragraph_score = 1.0 if paragraph_count else 0.0
    score = (text_ratio * 0.35) + (term_ratio * 0.45) + (paragraph_score * 0.2)
    return {
        "score": round(score, 3),
        "text_ratio": round(text_ratio, 3),
        "term_ratio": round(term_ratio, 3),
        "paragraph_count": paragraph_count,
    }


def parsed_text_is_grounded(text: str, source_text: str) -> bool:
    text_terms = set(_extract_keywords(text)[:12])
    if not text_terms:
        return len(text) <= len(source_text) + 100
    source_terms = set(_extract_keywords(source_text)[:80])
    overlap = len(text_terms & source_terms) / len(text_terms)
    return overlap >= 0.45


def analyze_topics_with_agent(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    client = get_openai_client()
    if client is None:
        result = fallback_topic_analysis(chunks)
        result["metadata"] = {
            "agent_used": "fallback",
            "reason": "LLM provider API key is not configured",
        }
        record_llm_call("topic_extraction", "fallback", "LLM provider API key is not configured")
        return result

    numbered_chunks = "\n\n".join(
        (
            f"chunk_index={index}\n"
            f"pages={chunk.get('page_start')}-{chunk.get('page_end')}\n"
            f"paragraph_ids={','.join(paragraph.get('paragraph_id', '') for paragraph in chunk.get('paragraphs', [])[:20])}\n"
            f"text={str(chunk.get('text', ''))[:2500]}"
        )
        for index, chunk in enumerate(chunks)
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a document ingestion agent. Split PDF chunks into coherent "
                "subtopics for MongoDB storage. Use grounded topic names from headings, "
                "keywords, and repeated concepts in the text. Return only valid JSON with this shape: "
                '{"topics":[{"topic":"string","summary":"string",'
                '"keywords":["string"],"chunk_indexes":[0]}]}. '
                "Every chunk_index must appear exactly once. Keywords must appear in the supplied text. "
                "Summaries must be factual and based only on the chunks."
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
        quality = evaluate_topic_analysis(result["topics"], chunks)
        result["metadata"] = {
            "agent_used": "llm",
            "reason": None,
            "quality": quality,
        }
        if quality["score"] < 0.55:
            fallback = fallback_topic_analysis(chunks)
            fallback["metadata"] = {
                "agent_used": "fallback",
                "reason": f"LLM topic quality score too low: {quality['score']}",
                "quality": quality,
            }
            record_llm_call("topic_extraction", "fallback", fallback["metadata"]["reason"])
            return fallback
        record_llm_call("topic_extraction", "llm", None)
        return result
    except Exception as exc:
        result = fallback_topic_analysis(chunks)
        result["metadata"] = {"agent_used": "fallback", "reason": str(exc)}
        record_llm_call("topic_extraction", "fallback", str(exc))
        return result


def generate_text(client: OpenAI, messages: list[dict[str, str]]) -> str:
    provider = get_active_provider()
    try:
        response = client.responses.create(
            model=provider["model"],
            input=messages,
        )
        logger.info("LLM call succeeded through Responses API")
        return response.output_text
    except Exception as responses_exc:
        logger.warning("Responses API call failed; trying Chat Completions: %s", responses_exc)
        response = client.chat.completions.create(
            model=provider["model"],
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
        logger.info("AI task=%s completed with provider", task)
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
        text_pool = " ".join(chunks[index]["text"] for index in chunk_indexes)
        keywords = [
            str(keyword).strip()[:40]
            for keyword in raw_topic.get("keywords", [])
            if keyword_is_grounded(str(keyword), text_pool)
        ][:8]
        if len(keywords) < 3:
            keywords = merge_keywords(keywords, _extract_keywords(text_pool), limit=8)
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


def evaluate_topic_analysis(
    topics: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = set(range(len(chunks)))
    assigned = [
        index
        for topic in topics
        for index in topic.get("chunk_indexes", [])
        if isinstance(index, int)
    ]
    assigned_set = set(assigned)
    missing = sorted(expected - assigned_set)
    duplicates = sorted(index for index, count in Counter(assigned).items() if count > 1)

    keyword_checks = 0
    grounded_keywords = 0
    summary_checks = 0
    usable_summaries = 0
    for topic in topics:
        chunk_indexes = [
            index
            for index in topic.get("chunk_indexes", [])
            if isinstance(index, int) and 0 <= index < len(chunks)
        ]
        text_pool = " ".join(str(chunks[index].get("text", "")) for index in chunk_indexes)
        for keyword in topic.get("keywords", []):
            keyword_checks += 1
            if keyword_is_grounded(str(keyword), text_pool):
                grounded_keywords += 1
        summary_checks += 1
        if summary_is_usable(str(topic.get("summary", "")), text_pool):
            usable_summaries += 1

    coverage_ratio = len(assigned_set) / len(expected) if expected else 1.0
    keyword_ratio = grounded_keywords / keyword_checks if keyword_checks else 0.0
    summary_ratio = usable_summaries / summary_checks if summary_checks else 0.0
    duplicate_penalty = min(len(duplicates) * 0.1, 0.3)
    score = max((coverage_ratio * 0.45) + (keyword_ratio * 0.3) + (summary_ratio * 0.25) - duplicate_penalty, 0)
    return {
        "score": round(score, 3),
        "coverage_ratio": round(coverage_ratio, 3),
        "keyword_grounding_ratio": round(keyword_ratio, 3),
        "summary_ratio": round(summary_ratio, 3),
        "missing_chunk_indexes": missing,
        "duplicate_chunk_indexes": duplicates,
    }


def keyword_is_grounded(keyword: str, text: str) -> bool:
    clean = keyword.strip().lower()
    if len(clean) < 2:
        return False
    return clean in text.lower()


def summary_is_usable(summary: str, text: str) -> bool:
    clean = " ".join(summary.split())
    if len(clean) < 20:
        return False
    if clean.lower() in {"no summary", "n/a", "none", "미분류"}:
        return False
    summary_terms = set(_extract_keywords(clean)[:5])
    text_terms = set(_extract_keywords(text)[:20])
    return not summary_terms or bool(summary_terms & text_terms)


def merge_keywords(primary: list[str], fallback: list[str], limit: int) -> list[str]:
    merged = []
    seen = set()
    for keyword in primary + fallback:
        clean = str(keyword).strip()
        key = clean.lower()
        if clean and key not in seen:
            merged.append(clean)
            seen.add(key)
        if len(merged) >= limit:
            break
    return merged


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
