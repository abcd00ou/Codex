from pathlib import Path
import re
from typing import Any

import fitz


def extract_pdf_pages(path: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            paragraphs, layout_objects = extract_page_layout(page, index)
            text = "\n\n".join(paragraph["text"] for paragraph in paragraphs).strip()
            pages.append(
                {
                    "page": index,
                    "width": round(float(page.rect.width), 2),
                    "height": round(float(page.rect.height), 2),
                    "text": text,
                    "paragraphs": paragraphs,
                    "layout_objects": layout_objects,
                }
            )
    return pages


def extract_page_layout(page: fitz.Page, page_number: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocks = []
    layout_objects = []
    for block in page.get_text("blocks"):
        if len(block) < 7:
            continue
        x0, y0, x1, y1, text, block_no, block_type = block[:7]
        bbox = [
            round(float(x0), 2),
            round(float(y0), 2),
            round(float(x1), 2),
            round(float(y1), 2),
        ]
        if block_type != 0:
            layout_objects.append(
                {
                    "object_id": f"obj{page_number}_{int(block_no)}",
                    "page": page_number,
                    "kind": "image_or_graphic",
                    "bbox": bbox,
                }
            )
            continue
        normalized = normalize_block_text(str(text))
        if normalized:
            blocks.append(
                {
                    "block_no": int(block_no),
                    "bbox": bbox,
                    "text": normalized,
                }
            )

    layout_objects.extend(extract_visual_objects(page, page_number))
    blocks.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    if not blocks:
        fallback = normalize_block_text(page.get_text("text"))
        if not fallback:
            return [], layout_objects
        blocks = [{"block_no": 0, "bbox": [0.0, 0.0, 0.0, 0.0], "text": fallback}]

    paragraphs = []
    paragraph_index = 1
    for block in blocks:
        for text in split_paragraphs(block["text"]):
            paragraphs.append(
                {
                    "paragraph_id": f"p{page_number}_{paragraph_index}",
                    "page": page_number,
                    "paragraph_index": paragraph_index,
                    "source_block_no": block["block_no"],
                    "bbox": block["bbox"],
                    "text": text,
                }
            )
            paragraph_index += 1
    return paragraphs, layout_objects


def extract_visual_objects(page: fitz.Page, page_number: int) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    seen: set[tuple[float, float, float, float]] = set()

    for image_index, image in enumerate(page.get_images(full=True), start=1):
        xref = image[0]
        for rect in page.get_image_rects(xref):
            bbox = tuple(round(float(value), 2) for value in (rect.x0, rect.y0, rect.x1, rect.y1))
            if bbox in seen:
                continue
            seen.add(bbox)
            objects.append(
                {
                    "object_id": f"img{page_number}_{image_index}",
                    "page": page_number,
                    "kind": "image",
                    "bbox": list(bbox),
                }
            )

    drawing_rects = []
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        width = float(rect.width)
        height = float(rect.height)
        if width < 24 or height < 24:
            continue
        drawing_rects.append(rect)

    for drawing_index, rect in enumerate(drawing_rects[:20], start=1):
        bbox = tuple(round(float(value), 2) for value in (rect.x0, rect.y0, rect.x1, rect.y1))
        if bbox in seen:
            continue
        seen.add(bbox)
        objects.append(
            {
                "object_id": f"draw{page_number}_{drawing_index}",
                "page": page_number,
                "kind": "graphic_or_chart",
                "bbox": list(bbox),
            }
        )
    return objects


def merge_document_paragraphs(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for page in pages:
        for paragraph in page.get("paragraphs") or []:
            current = dict(paragraph)
            current["text"] = clean_parser_text(str(current.get("text", "")))
            if looks_like_artifact_text(str(current.get("text", ""))):
                continue
            if merged and should_merge_paragraphs(merged[-1], current):
                merged[-1] = merge_two_paragraphs(merged[-1], current)
            else:
                merged.append(current)

    by_page: dict[int, list[dict[str, Any]]] = {int(page["page"]): [] for page in pages}
    kept_index = 0
    for source_index, paragraph in enumerate(merged, start=1):
        paragraph = annotate_paragraph_kind(paragraph, source_index)
        if paragraph.get("kind") == "table":
            continue
        kept_index += 1
        source_pages = sorted(set(paragraph.get("pages") or [paragraph.get("page")]))
        source_ids = paragraph.get("source_ids") or [paragraph.get("paragraph_id")]
        paragraph["paragraph_id"] = f"para_{kept_index:04d}"
        paragraph["document_paragraph_index"] = kept_index
        paragraph["paragraph_index"] = kept_index
        paragraph["source_pages"] = source_pages
        paragraph["source_ids"] = source_ids
        primary_page = int(source_pages[0])
        paragraph["page"] = primary_page
        by_page.setdefault(primary_page, []).append(paragraph)

    updated_pages = []
    for page in pages:
        page_number = int(page["page"])
        page_paragraphs = by_page.get(page_number, [])
        updated_page = dict(page)
        updated_page["paragraphs"] = page_paragraphs
        updated_page["text"] = "\n\n".join(str(item.get("text", "")) for item in page_paragraphs).strip()
        updated_pages.append(updated_page)
    return updated_pages


def annotate_paragraph_kind(paragraph: dict[str, Any], index: int) -> dict[str, Any]:
    item = dict(paragraph)
    if item.get("kind"):
        return item

    text = str(item.get("text", "")).strip()
    if index == 1 and looks_like_document_title(text):
        item["kind"] = "title"
    elif looks_like_section_heading(text):
        item["kind"] = "heading"
    elif looks_like_table_text(text):
        item["kind"] = "table"
    else:
        item["kind"] = "paragraph"
    return item


def looks_like_document_title(text: str) -> bool:
    clean = " ".join(text.split())
    if not clean or len(clean) > 160:
        return False
    title_terms = (
        "digest",
        "insights",
        "monthly",
        "report",
        "supply chain",
        "semiconductor",
        "intelligence",
    )
    has_title_term = any(term in clean.lower() for term in title_terms)
    has_date = bool(re.search(r"\b(20\d{2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\b", clean, re.I))
    return has_title_term or has_date


def looks_like_section_heading(text: str) -> bool:
    clean = " ".join(text.split())
    if len(clean) > 120:
        return False
    heading_terms = (
        "key takeaways",
        "other key takeaways",
        "top 4 channel comments",
        "conclusion",
        "appendix",
    )
    return any(term == clean.lower().rstrip(":") for term in heading_terms) or clean.endswith(":")


def looks_like_table_text(text: str) -> bool:
    clean = " ".join(text.split())
    lowered = clean.lower()
    tokens = clean.split()
    if re.match(r"^[+-]?\d+(\.\d+)?%$", clean):
        return True
    if re.match(r"^\$?\d+(\.\d+)?([-/]\$?\d+(\.\d+)?)*\+?$", clean):
        return True
    if "average contract price forecast" in lowered:
        return True
    if lowered.startswith("source:") and "estimate" in lowered and len(clean) <= 120:
        return True
    numeric_like_tokens = [
        token
        for token in tokens
        if re.match(r"^[+-]?\$?\d+(\.\d+)?%?$", token.strip(",;()"))
        or re.match(r"^\$?\d+(\.\d+)?[-/]\$?\d+(\.\d+)?\+?$", token.strip(",;()"))
    ]
    month_markers = re.findall(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-\s']?\d{2}\b", lowered)
    if len(month_markers) >= 3:
        return True
    if any(marker in lowered for marker in ("y/y", "m/m", "q/q")) and len(numeric_like_tokens) >= 2:
        return True
    if len(tokens) >= 4 and len(numeric_like_tokens) / max(len(tokens), 1) >= 0.6:
        return True
    if len(clean) < 80:
        return False
    table_terms = ("jan-23", "feb-23", "mar-23", "qtr avg", "price", "m/m")
    if sum(1 for term in table_terms if term in lowered) >= 3:
        return True
    return False


def clean_parser_text(text: str) -> str:
    clean = " ".join(text.split()).strip()
    if not clean:
        return ""

    clean = re.sub(r"\bImportant Disclosures in the Appendix\b", "", clean, flags=re.I).strip()
    clean = re.sub(
        r"^\*?\*?\s*Below is the abbreviated version of our .*?Insights Report\s*\*?\*?\s*",
        "",
        clean,
        flags=re.I,
    ).strip()
    clean = re.sub(
        r"^Note:\s+This is not the full Insights report,.*?requirements\s*",
        "",
        clean,
        flags=re.I,
    ).strip()
    clean = re.sub(
        r"^discuss the requirements(\s+|$)",
        "",
        clean,
        flags=re.I,
    ).strip()
    clean = re.sub(r"\s+discuss the requirements$", "", clean, flags=re.I).strip()
    return clean


def should_merge_paragraphs(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    if current.get("merge_with_previous"):
        return True
    previous_pages = previous.get("pages") or [previous.get("page")]
    current_page = int(current.get("page", 0))
    previous_page = int(previous_pages[-1] or 0)
    same_page = current_page == previous_page
    next_page = current_page == previous_page + 1
    if not same_page and not next_page:
        return False
    if str(current.get("kind", "paragraph")) in {"heading", "list", "table", "figure_caption"}:
        return False

    previous_text = str(previous.get("text", "")).strip()
    current_text = str(current.get("text", "")).strip()
    if not previous_text or not current_text:
        return False
    if looks_like_table_text(current_text):
        return False
    if same_page:
        return should_merge_same_page_fragment(previous, current)
    if re.search(r"[.!?。！？다요]\s*$", previous_text):
        return False
    if looks_like_heading_or_item(current_text[:120]):
        return False
    return bool(re.match(r"^[a-z가-힣,(]", current_text))


def should_merge_same_page_fragment(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    previous_text = str(previous.get("text", "")).strip()
    current_text = str(current.get("text", "")).strip()
    if looks_like_heading_or_item(current_text[:120]):
        return False

    previous_bbox = previous.get("bbox") or []
    current_bbox = current.get("bbox") or []
    same_column = True
    if len(previous_bbox) >= 2 and len(current_bbox) >= 2:
        same_column = abs(float(previous_bbox[0]) - float(current_bbox[0])) < 30

    starts_like_continuation = bool(re.match(r"^[a-z가-힣,(~$]", current_text))
    starts_with_acronym_continuation = bool(re.match(r"^[A-Z]{2,}[,\)]", current_text))
    starts_with_numbered_fact = bool(re.match(r"^\d+[\.\)]\s+\S", current_text))
    current_is_short_fragment = len(current_text) <= 50 and len(current_text.split()) <= 5
    previous_ends_with_connector = bool(re.search(r"\b(to|with|for|and|or|of|in|on|re|vs\.?)$", previous_text, re.I))
    previous_is_section_label = len(previous_text) <= 80 and previous_text.endswith(":")

    return same_column and (
        starts_like_continuation
        or starts_with_acronym_continuation
        or starts_with_numbered_fact
        or current_is_short_fragment
        or previous_ends_with_connector
        or previous_is_section_label
    )


def looks_like_artifact_text(text: str) -> bool:
    clean = " ".join(text.split()).strip()
    lowered = clean.lower()
    if not clean:
        return True
    if len(clean) <= 120 and (
        "solely intended for use" in lowered
        or "not for redistribution" in lowered
        or "important disclosures in the appendix" == lowered
    ):
        return True
    if clean.upper() == "APPENDIX":
        return True
    if lowered in {"analog semiconductor insights"}:
        return True
    if lowered.startswith("note: this is not the full insights report"):
        return True
    if lowered.startswith("volume ") and " issue " in lowered and re.search(r"\b20\d{2}\b", lowered):
        return True
    if re.match(r"^(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+20\d{2}$", clean, re.I):
        return True
    if lowered.startswith("appendix ") and "certify that the views expressed" in lowered:
        return True
    if lowered.startswith("we, ") and "certify that the views expressed" in lowered:
        return True
    if len(re.findall(r"[\w.+-]+@[\w.-]+", clean)) >= 2:
        return True
    if len(re.findall(r"\b\d{3}[.\-\s]\d{3}[.\-\s]\d{4}\b", clean)) >= 2:
        return True
    if re.match(r"^page\s+\d+(\s+of\s+\d+)?$", lowered):
        return True
    if re.match(r"^issn[:\s-]*[\d-]+", lowered):
        return True
    return False


def merge_two_paragraphs(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    previous_text = str(previous.get("text", "")).rstrip()
    current_text = str(current.get("text", "")).lstrip()
    separator = "" if previous_text.endswith("-") else " "
    if previous_text.endswith("-"):
        previous_text = previous_text[:-1]
    merged = dict(previous)
    merged["text"] = f"{previous_text}{separator}{current_text}".strip()
    merged["pages"] = sorted(set((previous.get("pages") or [previous.get("page")]) + [current.get("page")]))
    merged["source_ids"] = (previous.get("source_ids") or [previous.get("paragraph_id")]) + (
        current.get("source_ids") or [current.get("paragraph_id")]
    )
    merged["continued_across_pages"] = True
    return merged


def normalize_block_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\x00", "").splitlines()]
    kept = [line for line in lines if line]
    return "\n".join(kept).strip()


def split_paragraphs(text: str) -> list[str]:
    raw_parts = [part.strip() for part in text.split("\n\n") if part.strip()]
    if len(raw_parts) > 1:
        return [" ".join(part.split()) for part in raw_parts]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    paragraphs = []
    current = []
    for line in lines:
        starts_new = bool(current) and looks_like_heading_or_item(line)
        if starts_new:
            paragraphs.append(" ".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        paragraphs.append(" ".join(current).strip())
    return paragraphs


def looks_like_heading_or_item(line: str) -> bool:
    if len(line) <= 80 and line.endswith(":"):
        return True
    prefixes = ("-", "*", "•", "·")
    if line.startswith(prefixes):
        return True
    return bool(re.match(r"^([A-Z][\.\)]|제\s*\d+\s*[장절])\s+", line))


def chunk_pages(
    pages: list[dict[str, Any]],
    max_chars: int,
    overlap_chars: int,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_text = ""
    current_paragraphs: list[dict[str, Any]] = []
    page_start: int | None = None
    page_end = 0

    for page in pages:
        page_number = int(page["page"])
        paragraphs = page.get("paragraphs") or []
        for paragraph in paragraphs:
            paragraph_text = str(paragraph.get("text", "")).strip()
            if not paragraph_text:
                continue

            paragraph_blocks = split_long_paragraph(paragraph, max_chars)
            for paragraph_block, block_paragraph in paragraph_blocks:
                if page_start is None:
                    page_start = page_number

                candidate = f"{current_text}\n\n{paragraph_block}".strip()
                if len(candidate) <= max_chars:
                    current_text = candidate
                    current_paragraphs.append(block_paragraph)
                    page_end = page_number
                    continue

                if current_text and page_start is not None:
                    chunks.append(
                        {
                            "page_start": page_start,
                            "page_end": page_end,
                            "text": current_text,
                            "paragraphs": current_paragraphs,
                        }
                    )

                current_text = paragraph_block
                current_paragraphs = [block_paragraph]
                page_start = page_number
                page_end = page_number

    if current_text and page_start is not None:
        chunks.append(
            {
                "page_start": page_start,
                "page_end": page_end,
                "text": current_text,
                "paragraphs": current_paragraphs,
            }
        )

    return chunks


def split_long_paragraph(
    paragraph: dict[str, Any],
    max_chars: int,
) -> list[tuple[str, dict[str, Any]]]:
    paragraph_id = str(paragraph.get("paragraph_id", "p_unknown"))
    text = str(paragraph.get("text", "")).strip()
    available_chars = max(max_chars, 500)

    if len(text) <= available_chars:
        return [(text, paragraph)]

    parts = split_text_by_sentence(text, available_chars)
    blocks = []
    for part_index, part in enumerate(parts, start=1):
        part_paragraph = dict(paragraph)
        part_paragraph["paragraph_id"] = f"{paragraph_id}_{part_index}"
        part_paragraph["text"] = part
        blocks.append((part, part_paragraph))
    return blocks


def split_text_by_sentence(text: str, max_chars: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？다요])\s+", text)
    parts: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                parts.append(current)
                current = ""
            parts.extend(sentence[index : index + max_chars] for index in range(0, len(sentence), max_chars))
            continue
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                parts.append(current)
            current = sentence

    if current:
        parts.append(current)
    return parts
