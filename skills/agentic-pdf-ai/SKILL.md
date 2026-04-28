---
name: agentic-pdf-ai
description: "Use when building, debugging, or extending this gpt-oss-120B PDF ingestion system: PDF parsing, topic extraction, MongoDB/local storage, report generation, dashboard aggregation, API testing, and quality controls for weaker model reliability."
---

# Agentic PDF AI

Use this skill to maintain the PDF ingestion/reporting API in this repository. The system must work with `gpt-oss-120B` as the only LLM, so prefer deterministic code, schema validation, and fallback paths over trusting model output.

## Core Rule

Do not design flows where the model is the only source of correctness. The model may classify, summarize, and propose metadata, but the application must preserve raw text, page ranges, chunk IDs, and validation state.

## Architecture

- FastAPI exposes `/v1` endpoints.
- `app/services/pdf_parser.py` extracts page text and creates chunks.
- `app/services/llm.py` calls `gpt-oss-120B` and provides fallback logic.
- `app/routes/documents.py` stores documents, topics, and chunks.
- `app/routes/reports.py` retrieves chunks and summarizes them.
- `app/routes/dashboard.py` aggregates stored data.
- `app/database.py` uses MongoDB when `MONGODB_URI` is MongoDB-like.
- `app/local_store.py` provides development storage when `MONGODB_URI=local://dev`.

## Required Workflow

1. Parse PDF text with deterministic code.
2. Chunk by bounded size before calling the model.
3. Ask the topic agent for JSON only.
4. Parse and normalize the JSON.
5. If parsing fails, run fallback topic extraction.
6. Store raw chunk text regardless of model quality.
7. Store topic metadata separately in `document_topics`.
8. Attach `topic_id`, `topic`, `topic_summary`, and `keywords` to each chunk.
9. Include sources in report responses.
10. Verify with API calls before finishing changes.

## gpt-oss-120B Prompting Rules

- Keep prompts short and concrete.
- Ask for one job per call.
- Require exact JSON shape for extraction tasks.
- Avoid broad instructions like "analyze everything deeply".
- Include chunk indexes and require every index exactly once.
- Treat invalid or partial JSON as expected, not exceptional.
- Use deterministic fallback rather than repeated blind retries.

Preferred extraction contract:

```json
{
  "topics": [
    {
      "topic": "string",
      "summary": "string",
      "keywords": ["string"],
      "chunk_indexes": [0]
    }
  ]
}
```

## Reliability Pattern

When adding an agent feature, implement all four layers:

1. Prompt: clear role, exact output shape, bounded context.
2. Parser: strict JSON extraction or structured parser.
3. Normalizer: enforce types, bounds, defaults, missing chunk coverage.
4. Fallback: deterministic behavior if the model fails.

Never add a new model call without a fallback path.

## MongoDB Rules

Use these collections:

- `documents`: PDF-level metadata.
- `document_topics`: topic name, summary, keywords, page range, chunk IDs.
- `document_chunks`: raw chunk text plus topic metadata.
- `reports`: generated report history.
- `dashboard_snapshots`: dashboard aggregate results.

Indexes should support:

- document lookup by `document_id`
- topic lookup by `document_id`
- chunk text search
- text search over topic, summary, keywords

For local development, keep behavior compatible with `app/local_store.py`.

## API Verification

After changes, run:

```bash
.venv/bin/python -m compileall app
curl -s http://127.0.0.1:8000/v1
curl -s -X POST http://127.0.0.1:8000/v1/dashboard/refresh
```

If a sample PDF exists, test upload:

```bash
curl -s -F file=@test_assets/sample.pdf http://127.0.0.1:8000/v1/documents
```

Then verify:

```bash
curl -s http://127.0.0.1:8000/v1/documents/<document_id>/topics
```

## Report Quality

Reports must:

- summarize only retrieved chunks
- include source chunk IDs
- include document IDs
- include page ranges
- include topic metadata when available
- state when no relevant material is found

Do not let the report agent invent facts not present in stored chunks.

## Dashboard Quality

Dashboard endpoints should aggregate database state. Use model output only for metadata suggestions or chart configuration proposals, and validate those proposals before storing them.

## Common Failure Modes

- Model returns prose instead of JSON: extract JSON block or fallback.
- Model omits a chunk index: assign missing chunks to fallback topics.
- Model duplicates a chunk index: keep the first valid assignment.
- MongoDB is unavailable: use `MONGODB_URI=local://dev`.
- Local MongoDB install fails: prefer MongoDB Atlas or Docker Desktop.
- Topic names are too broad: derive fallback names from headings and keywords.

## Done Criteria

A change is not done until:

- code compiles
- server starts
- `/v1` returns `status: ok`
- upload path works or the blocker is documented
- topic records are inspectable through `/v1/documents/{document_id}/topics`
- report source chunks include traceable IDs and page ranges
