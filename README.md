# Agentic PDF AI

PDF를 업로드하면 내용을 파싱하고, 소주제별로 나누어 저장한 뒤, 저장된 자료를 검색/요약/대시보드 데이터로 제공하는 FastAPI 기반 agentic AI API입니다.

이 프로젝트는 `gpt-oss-120B`만 사용할 수 있는 환경을 전제로 합니다. 모델 성능이 항상 안정적이라고 가정하지 않고, 파서, schema 검증, fallback 로직, 짧은 agent 역할 분리로 품질을 보완합니다.

## What It Does

- PDF 업로드
- PDF 텍스트 추출
- chunk 생성
- agent 기반 소주제 분리
- 문서, 소주제, chunk 저장
- 관련 자료 검색
- 리포트 생성
- 대시보드 집계 데이터 생성

## Architecture

```txt
Client / Swagger
  -> FastAPI
    -> PDF parser
    -> Topic extraction agent
    -> Storage
       - local JSON for development
       - MongoDB / MongoDB Atlas for production
    -> Report agent
    -> Dashboard aggregation
```

## Requirements

- Python 3.13+
- `gpt-oss-120B` OpenAI-compatible API endpoint, or OpenAI API endpoint that supports your configured model
- MongoDB or MongoDB Atlas for production

For local development, MongoDB is optional because `MONGODB_URI=local://dev` stores data in `.storage/local_db.json`.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Environment

Open `.env` and configure one of the storage modes.

Development mode without MongoDB:

```env
MONGODB_URI=local://dev
MONGODB_DB=agentic_ai
```

Local MongoDB:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=agentic_ai
```

MongoDB Atlas:

```env
MONGODB_URI=mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=agentic_ai
```

`gpt-oss-120B` OpenAI-compatible endpoint:

```env
OPENAI_API_KEY=local-key
OPENAI_BASE_URL=http://localhost:8001/v1
OPENAI_MODEL=gpt-oss-120b
```

Keep the model server on a different port from this API. This FastAPI app uses port `8000`; a local model server should use something like `8001`.

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

- API health: http://127.0.0.1:8000/v1
- Swagger: http://127.0.0.1:8000/docs

## API Test Flow

1. Open Swagger at http://127.0.0.1:8000/docs
2. Run `POST /v1/documents`
3. Upload a PDF file
4. Copy the returned `document_id`
5. Run `GET /v1/documents/{document_id}`
6. Run `GET /v1/documents/{document_id}/topics`
7. Run `POST /v1/reports`
8. Run `POST /v1/dashboard/refresh`

Example report body:

```json
{
  "query": "이 문서의 핵심 리스크와 주요 지표를 소주제별로 요약해줘",
  "limit": 5
}
```

## Data Model

`documents`

- One record per uploaded PDF
- Stores filename, path, page count, upload time, chunk count, topic count

`document_topics`

- One record per agent-generated topic
- Stores topic name, summary, keywords, page range, related chunk IDs

`document_chunks`

- Searchable parsed PDF text
- Stores chunk text, page range, topic metadata, keywords

`reports`

- Generated report history
- Stores query, answer, source chunks

`dashboard_snapshots`

- Aggregated dashboard state
- Stores document count, topic count, chunk count, recent documents

## Agent Strategy For gpt-oss-120B

Do not ask the model to do everything in one pass. Use small jobs:

- Parser extracts text deterministically.
- Chunker limits input size.
- Topic agent only returns structured JSON.
- Normalizer validates topic output.
- Fallback topic splitter runs when JSON is invalid or the model is unavailable.
- Report agent summarizes only retrieved chunks.
- Dashboard logic uses database aggregation, not free-form model output.

This keeps the system useful even when `gpt-oss-120B` is weaker than frontier closed models.

## Quality Controls

- Always preserve source page ranges.
- Always store raw chunk text.
- Never overwrite parser output with model output.
- Treat model-generated topics as metadata, not ground truth.
- Validate model JSON before storing.
- Store source chunk IDs in every topic.
- Include source chunks in every report response.
- Keep a local fallback path for development and outages.

## Current Local Note

On this machine, Homebrew MongoDB installation was blocked because the installed Xcode version was too old for the MongoDB formula. Use one of these options:

- Continue development with `MONGODB_URI=local://dev`
- Use MongoDB Atlas
- Install/update Xcode and then install MongoDB locally
- Use Docker Desktop, then run `docker compose up -d mongodb`

## Project Skill

The project includes an agent operating guide:

```txt
skills/agentic-pdf-ai/SKILL.md
```

Use it as the instruction source when asking an AI coding agent to extend this system.

## Project Coding Agent MVP

This repository includes a small project-specific coding agent CLI:

```txt
tools/coder_agent.py
```

It reads the repository README, the project skill, and selected source files, then asks `gpt-oss-120B` for either an implementation plan or a unified diff patch.

The default mode is safe: it prints the generated patch but does not apply it.
The CLI tries the Responses API first and falls back to Chat Completions for local OpenAI-compatible `gpt-oss-120B` servers.

Generate a plan:

```bash
.venv/bin/python tools/coder_agent.py \
  "topic extraction fallback 품질을 개선해줘" \
  --mode plan
```

Generate a patch without applying it:

```bash
.venv/bin/python tools/coder_agent.py \
  "topic extraction fallback 품질을 개선해줘"
```

Save the patch to a file:

```bash
.venv/bin/python tools/coder_agent.py \
  "topic extraction fallback 품질을 개선해줘" \
  --output proposed.patch
```

Apply and verify the patch:

```bash
.venv/bin/python tools/coder_agent.py \
  "topic extraction fallback 품질을 개선해줘" \
  --apply \
  --verify
```

Add extra files to context:

```bash
.venv/bin/python tools/coder_agent.py \
  "report source citation 품질을 개선해줘" \
  --file app/routes/reports.py \
  --file app/services/llm.py
```

Recommended workflow:

1. Run `--mode plan` first.
2. Generate a patch without `--apply`.
3. Read the patch.
4. Re-run with `--apply --verify` only if the patch is acceptable.
5. Test through Swagger.

This tool is intentionally narrow. It is not a general coding assistant; it is tuned for this PDF ingestion API and the `gpt-oss-120B` reliability constraints.

## Useful Commands

Compile check:

```bash
.venv/bin/python -m compileall app
```

Health check:

```bash
curl -s http://127.0.0.1:8000/v1
```

Dashboard refresh:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/dashboard/refresh
```

Upload PDF:

```bash
curl -s -F file=@path/to/file.pdf http://127.0.0.1:8000/v1/documents
```

Create report:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/reports \
  -H 'Content-Type: application/json' \
  -d '{"query":"핵심 리스크를 소주제별로 요약","limit":5}'
```
