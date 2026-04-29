from pathlib import Path
import re
from typing import Any

import fitz


def extract_pdf_pages(path: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            paragraphs = extract_page_paragraphs(page, index)
            text = "\n\n".join(paragraph["text"] for paragraph in paragraphs).strip()
            pages.append({"page": index, "text": text, "paragraphs": paragraphs})
    return pages


def extract_page_paragraphs(page: fitz.Page, page_number: int) -> list[dict[str, Any]]:
    blocks = []
    for block in page.get_text("blocks"):
        if len(block) < 7:
            continue
        x0, y0, _x1, _y1, text, _block_no, block_type = block[:7]
        if block_type != 0:
            continue
        normalized = normalize_block_text(str(text))
        if normalized:
            blocks.append((round(float(y0), 2), round(float(x0), 2), normalized))

    blocks.sort(key=lambda item: (item[0], item[1]))
    if not blocks:
        fallback = normalize_block_text(page.get_text("text"))
        if not fallback:
            return []
        blocks = [(0.0, 0.0, fallback)]

    paragraphs = []
    paragraph_index = 1
    for _y, _x, block_text in blocks:
        for text in split_paragraphs(block_text):
            paragraphs.append(
                {
                    "paragraph_id": f"p{page_number}_{paragraph_index}",
                    "page": page_number,
                    "paragraph_index": paragraph_index,
                    "text": text,
                }
            )
            paragraph_index += 1
    return paragraphs


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
    return bool(re.match(r"^(\d+[\.\)]|[A-Z][\.\)]|제\s*\d+\s*[장절])\s+", line))


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
    page_number = int(paragraph.get("page", 0))
    text = str(paragraph.get("text", "")).strip()
    prefix = f"[page {page_number} | {paragraph_id}]"
    available_chars = max(max_chars - len(prefix) - 2, 500)

    if len(text) <= available_chars:
        return [(f"{prefix}\n{text}", paragraph)]

    parts = split_text_by_sentence(text, available_chars)
    blocks = []
    for part_index, part in enumerate(parts, start=1):
        part_paragraph = dict(paragraph)
        part_paragraph["paragraph_id"] = f"{paragraph_id}_{part_index}"
        part_paragraph["text"] = part
        part_prefix = f"[page {page_number} | {part_paragraph['paragraph_id']}]"
        blocks.append((f"{part_prefix}\n{part}", part_paragraph))
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
