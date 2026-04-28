from pathlib import Path

import fitz


def extract_pdf_pages(path: Path) -> list[dict[str, int | str]]:
    pages: list[dict[str, int | str]] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            pages.append({"page": index, "text": text})
    return pages


def chunk_pages(
    pages: list[dict[str, int | str]],
    max_chars: int,
    overlap_chars: int,
) -> list[dict[str, int | str]]:
    chunks: list[dict[str, int | str]] = []
    current_text = ""
    page_start: int | None = None
    page_end = 0

    for page in pages:
        page_number = int(page["page"])
        page_text = str(page["text"]).strip()
        if not page_text:
            continue

        if page_start is None:
            page_start = page_number

        candidate = f"{current_text}\n\n[page {page_number}]\n{page_text}".strip()
        if len(candidate) <= max_chars:
            current_text = candidate
            page_end = page_number
            continue

        if current_text:
            chunks.append(
                {
                    "page_start": page_start,
                    "page_end": page_end,
                    "text": current_text,
                }
            )
            overlap = current_text[-overlap_chars:] if overlap_chars > 0 else ""
            current_text = f"{overlap}\n\n[page {page_number}]\n{page_text}".strip()
            page_start = page_number
            page_end = page_number

        while len(current_text) > max_chars:
            part = current_text[:max_chars]
            chunks.append({"page_start": page_start, "page_end": page_end, "text": part})
            current_text = current_text[max_chars - overlap_chars :]

    if current_text and page_start is not None:
        chunks.append({"page_start": page_start, "page_end": page_end, "text": current_text})

    return chunks
