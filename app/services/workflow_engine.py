from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pymongo.database import Database

from app.local_store import LocalDatabase
from app.schemas import WorkflowRun, WorkflowRunRequest, WorkflowResumeRequest, WorkflowStep
from app.services.llm import generate_json, get_openai_client, record_llm_call, summarize_with_llm


MAX_STEP_ATTEMPTS = 2
MAX_PLANNED_STEPS = 6
ALLOWED_STEP_KINDS = {
    "llm_extract",
    "llm_summarize",
    "llm_review",
    "internal_search_documents",
    "internal_create_report",
}


def start_workflow_run(db: Database | LocalDatabase, request: WorkflowRunRequest) -> WorkflowRun:
    now = datetime.now(UTC)
    run = WorkflowRun(
        run_id=f"workflow_{uuid4().hex}",
        goal=request.goal.strip(),
        input_data=request.input_data,
        status="pending",
        steps=[
            WorkflowStep(
                step_id=f"step_{uuid4().hex}",
                name="Plan workflow",
                kind="llm_plan",
                input={"goal": request.goal.strip(), "input_data": request.input_data},
            )
        ],
        created_at=now,
        updated_at=now,
    )
    save_workflow_run(db, run)
    return execute_workflow_run(db, run, allow_resume=False)


def resume_workflow_run(
    db: Database | LocalDatabase,
    run: WorkflowRun,
    request: WorkflowResumeRequest,
) -> WorkflowRun:
    if run.status not in {"failed", "needs_input"}:
        raise ValueError("Only failed or needs_input workflow runs can be resumed")

    merged_input = {**run.input_data, **request.input_data}
    run.input_data = merged_input
    run.error = None
    run.questions = []
    for step in run.steps:
        if step.status in {"failed", "running"}:
            step.status = "pending"
            step.error = None
    if not any(step.status == "pending" for step in run.steps):
        run.steps.append(
            WorkflowStep(
                step_id=f"step_{uuid4().hex}",
                name="Plan workflow",
                kind="llm_plan",
                input={"goal": run.goal, "input_data": merged_input},
            )
        )
    save_workflow_run(db, run)
    return execute_workflow_run(db, run, allow_resume=True)


def get_workflow_run(db: Database | LocalDatabase, run_id: str) -> WorkflowRun | None:
    record = db.workflow_runs.find_one({"run_id": run_id}, {"_id": 0})
    if record is None:
        return None
    return WorkflowRun.model_validate(record)


def save_workflow_run(db: Database | LocalDatabase, run: WorkflowRun) -> None:
    run.updated_at = datetime.now(UTC)
    db.workflow_runs.replace_one(
        {"run_id": run.run_id},
        run.model_dump(mode="python"),
        upsert=True,
    )


def execute_workflow_run(
    db: Database | LocalDatabase,
    run: WorkflowRun,
    allow_resume: bool,
) -> WorkflowRun:
    if run.status == "failed" and not allow_resume:
        return run
    transition(run, "running")
    save_workflow_run(db, run)

    if goal_needs_input(run):
        run.status = "needs_input"
        run.questions = ["어떤 자료나 텍스트를 기준으로 워크플로우를 실행할까요?"]
        save_workflow_run(db, run)
        return run

    while True:
        step = next((item for item in run.steps if item.status == "pending"), None)
        if step is None:
            run.status = "succeeded"
            run.result = build_final_result(run)
            save_workflow_run(db, run)
            return run

        try:
            execute_step(db, run, step)
            save_workflow_run(db, run)
            if run.status == "needs_input":
                return run
        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)
            run.status = "failed"
            run.error = f"{step.name}: {exc}"
            save_workflow_run(db, run)
            return run


def transition(run: WorkflowRun, target: str) -> None:
    allowed = {
        "pending": {"running", "failed"},
        "running": {"succeeded", "failed", "needs_input"},
        "needs_input": {"running"},
        "failed": {"running"},
        "succeeded": set(),
    }
    if target not in allowed[run.status]:
        raise ValueError(f"Invalid workflow transition: {run.status} -> {target}")
    run.status = target


def goal_needs_input(run: WorkflowRun) -> bool:
    goal = run.goal.strip()
    if run.input_data:
        return False
    return len(goal) < 4


def execute_step(db: Database | LocalDatabase, run: WorkflowRun, step: WorkflowStep) -> None:
    last_error: Exception | None = None
    while step.attempts < MAX_STEP_ATTEMPTS:
        step.status = "running"
        step.attempts += 1
        try:
            if step.kind == "llm_plan":
                output = plan_workflow(run)
                step.output = output
                step.status = "succeeded"
                if output.get("questions") and not output.get("steps"):
                    run.questions = [str(question) for question in output["questions"]]
                    run.status = "needs_input"
                    step.error = None
                    return
                append_planned_steps(run, output.get("steps", []))
            elif step.kind == "llm_extract":
                step.output = llm_extract(run, step)
                step.status = "succeeded"
            elif step.kind == "llm_summarize":
                step.output = llm_summarize(run, step)
                step.status = "succeeded"
            elif step.kind == "llm_review":
                step.output = llm_review(run, step)
                step.status = "succeeded"
            elif step.kind == "internal_search_documents":
                step.output = internal_search_documents(db, run, step)
                step.status = "succeeded"
            elif step.kind == "internal_create_report":
                step.output = internal_create_report(db, run, step)
                step.status = "succeeded"
            else:
                raise ValueError(f"Unsupported workflow step kind: {step.kind}")

            verify_step_output(step)
            step.error = None
            return
        except Exception as exc:
            last_error = exc
            step.error = str(exc)
            step.status = "pending"

    step.status = "failed"
    raise ValueError(str(last_error) if last_error else "Step failed")


def plan_workflow(run: WorkflowRun) -> dict[str, Any]:
    client = get_openai_client()
    if client is None:
        record_llm_call("workflow_planning", "fallback", "LLM provider API key is not configured")
        return fallback_plan(run)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a deterministic workflow planner. Return only valid JSON with this shape: "
                '{"steps":[{"name":"string","kind":"llm_extract|llm_summarize|llm_review|'
                'internal_search_documents|internal_create_report","input":{}}],"questions":[]}. '
                "Use at most 6 steps. Ask questions only when the goal cannot be attempted from the input."
            ),
        },
        {
            "role": "user",
            "content": f"Goal:\n{run.goal}\n\nInput data:\n{run.input_data}",
        },
    ]
    try:
        data = generate_json(client, messages, "workflow_planning")
        steps = normalize_planned_steps(data.get("steps", []), run)
        questions = [
            str(question).strip()
            for question in data.get("questions", [])
            if str(question).strip()
        ][:3]
        if questions and not steps:
            return {"steps": [], "questions": questions, "planner": "llm"}
        if steps:
            return {"steps": steps, "questions": questions, "planner": "llm"}
        return fallback_plan(run)
    except Exception as exc:
        record_llm_call("workflow_planning", "fallback", str(exc))
        return fallback_plan(run)


def fallback_plan(run: WorkflowRun) -> dict[str, Any]:
    goal = run.goal.lower()
    input_data = run.input_data
    steps: list[dict[str, Any]] = []
    if "report" in goal or "리포트" in goal or "보고서" in goal:
        steps.extend(
            [
                {
                    "name": "Search stored documents",
                    "kind": "internal_search_documents",
                    "input": {"query": input_data.get("query") or run.goal, "limit": input_data.get("limit", 8)},
                },
                {
                    "name": "Create grounded report",
                    "kind": "internal_create_report",
                    "input": {"query": input_data.get("query") or run.goal},
                },
            ]
        )
    elif input_data.get("text"):
        if "extract" in goal or "추출" in goal:
            steps.append({"name": "Extract structured facts", "kind": "llm_extract", "input": {}})
        steps.append({"name": "Summarize input text", "kind": "llm_summarize", "input": {}})
    else:
        steps.extend(
            [
                {
                    "name": "Search stored documents",
                    "kind": "internal_search_documents",
                    "input": {"query": input_data.get("query") or run.goal, "limit": input_data.get("limit", 8)},
                },
                {"name": "Summarize search results", "kind": "llm_summarize", "input": {}},
            ]
        )
    steps.append({"name": "Review workflow result", "kind": "llm_review", "input": {}})
    return {"steps": steps[:MAX_PLANNED_STEPS], "questions": [], "planner": "fallback"}


def normalize_planned_steps(raw_steps: Any, run: WorkflowRun) -> list[dict[str, Any]]:
    if not isinstance(raw_steps, list):
        return []
    steps = []
    for index, raw_step in enumerate(raw_steps[:MAX_PLANNED_STEPS], start=1):
        if not isinstance(raw_step, dict):
            continue
        kind = str(raw_step.get("kind") or "").strip()
        if kind not in ALLOWED_STEP_KINDS:
            continue
        name = str(raw_step.get("name") or f"Step {index}").strip()[:120]
        step_input = raw_step.get("input") if isinstance(raw_step.get("input"), dict) else {}
        steps.append({"name": name, "kind": kind, "input": {"goal": run.goal, **step_input}})
    return steps


def append_planned_steps(run: WorkflowRun, planned_steps: list[dict[str, Any]]) -> None:
    if has_execution_plan(run):
        return
    for raw_step in planned_steps:
        run.steps.append(
            WorkflowStep(
                step_id=f"step_{uuid4().hex}",
                name=str(raw_step["name"]),
                kind=raw_step["kind"],
                input=raw_step.get("input", {}),
            )
        )


def llm_extract(run: WorkflowRun, step: WorkflowStep) -> dict[str, Any]:
    text = workflow_text_context(run)
    client = get_openai_client()
    if client is None:
        record_llm_call("workflow_extract", "fallback", "LLM provider API key is not configured")
        return {"facts": fallback_facts(text), "agent_used": "fallback"}
    messages = [
        {
            "role": "system",
            "content": (
                "Extract grounded facts from the provided text. Return only valid JSON with this shape: "
                '{"facts":[{"label":"string","value":"string","evidence":"string"}]}.'
            ),
        },
        {"role": "user", "content": f"Goal: {run.goal}\n\nText:\n{text[:12000]}"},
    ]
    try:
        data = generate_json(client, messages, "workflow_extract")
        facts = data.get("facts") if isinstance(data.get("facts"), list) else []
        return {"facts": facts[:20], "agent_used": "llm"}
    except Exception as exc:
        record_llm_call("workflow_extract", "fallback", str(exc))
        return {"facts": fallback_facts(text), "agent_used": "fallback", "reason": str(exc)}


def llm_summarize(run: WorkflowRun, step: WorkflowStep) -> dict[str, Any]:
    text = workflow_text_context(run)
    chunks = last_search_chunks(run)
    if chunks:
        answer = summarize_with_llm(run.goal, chunks)
        return {"summary": answer, "source_chunks": trim_source_chunks(chunks), "agent_used": "llm_or_fallback"}
    if not text:
        return {"summary": "요약할 입력 텍스트나 검색 결과가 없습니다.", "agent_used": "fallback"}
    client = get_openai_client()
    if client is None:
        record_llm_call("workflow_summarize", "fallback", "LLM provider API key is not configured")
        return {"summary": fallback_summary_text(text), "agent_used": "fallback"}
    messages = [
        {
            "role": "system",
            "content": "Summarize only from the provided text. Return only valid JSON: {\"summary\":\"string\"}.",
        },
        {"role": "user", "content": f"Goal: {run.goal}\n\nText:\n{text[:12000]}"},
    ]
    try:
        data = generate_json(client, messages, "workflow_summarize")
        summary = str(data.get("summary") or "").strip()
        if not summary:
            raise ValueError("Missing summary")
        return {"summary": summary, "agent_used": "llm"}
    except Exception as exc:
        record_llm_call("workflow_summarize", "fallback", str(exc))
        return {"summary": fallback_summary_text(text), "agent_used": "fallback", "reason": str(exc)}


def llm_review(run: WorkflowRun, step: WorkflowStep) -> dict[str, Any]:
    result_text = workflow_text_context(run, include_outputs=True)
    client = get_openai_client()
    if client is None:
        record_llm_call("workflow_review", "fallback", "LLM provider API key is not configured")
        return {
            "next_action": "final",
            "reason": "LLM provider API key is not configured; accepted deterministic output.",
            "final_answer": latest_answer_text(run) or fallback_summary_text(result_text),
            "agent_used": "fallback",
        }
    messages = [
        {
            "role": "system",
            "content": (
                "Review the workflow outputs for the goal. Return only valid JSON with this shape: "
                '{"next_action":"final|retry|needs_input","reason":"string","step_updates":[],'
                '"final_answer":"string"}.'
            ),
        },
        {"role": "user", "content": f"Goal: {run.goal}\n\nWorkflow outputs:\n{result_text[:12000]}"},
    ]
    try:
        data = generate_json(client, messages, "workflow_review")
        return {
            "next_action": str(data.get("next_action") or "final"),
            "reason": str(data.get("reason") or ""),
            "step_updates": data.get("step_updates") if isinstance(data.get("step_updates"), list) else [],
            "final_answer": str(data.get("final_answer") or fallback_summary_text(result_text)),
            "agent_used": "llm",
        }
    except Exception as exc:
        record_llm_call("workflow_review", "fallback", str(exc))
        return {
            "next_action": "final",
            "reason": str(exc),
            "final_answer": latest_answer_text(run) or fallback_summary_text(result_text),
            "agent_used": "fallback",
        }


def internal_search_documents(
    db: Database | LocalDatabase,
    run: WorkflowRun,
    step: WorkflowStep,
) -> dict[str, Any]:
    query = str(step.input.get("query") or run.input_data.get("query") or run.goal)
    limit = int(step.input.get("limit") or run.input_data.get("limit") or 8)
    chunks = list(
        db.document_chunks.find(
            {"$text": {"$search": query}},
            {
                "_id": 0,
                "chunk_id": 1,
                "document_id": 1,
                "page_start": 1,
                "page_end": 1,
                "topic_id": 1,
                "topic": 1,
                "topic_summary": 1,
                "keywords": 1,
                "text": 1,
                "metadata": 1,
                "score": {"$meta": "textScore"},
            },
        )
        .sort([("score", {"$meta": "textScore"})])
        .limit(limit)
    )
    if not chunks:
        chunks = list(
            db.document_chunks.find(
                {},
                {
                    "_id": 0,
                    "chunk_id": 1,
                    "document_id": 1,
                    "page_start": 1,
                    "page_end": 1,
                    "topic_id": 1,
                    "topic": 1,
                    "topic_summary": 1,
                    "keywords": 1,
                    "text": 1,
                    "metadata": 1,
                },
            ).limit(limit)
        )
    return {"query": query, "count": len(chunks), "chunks": chunks}


def internal_create_report(
    db: Database | LocalDatabase,
    run: WorkflowRun,
    step: WorkflowStep,
) -> dict[str, Any]:
    query = str(step.input.get("query") or run.input_data.get("query") or run.goal)
    chunks = last_search_chunks(run)
    if not chunks:
        search_step = WorkflowStep(
            step_id=f"step_{uuid4().hex}",
            name="Search stored documents",
            kind="internal_search_documents",
            input={"query": query, "limit": run.input_data.get("limit", 8)},
        )
        chunks = internal_search_documents(db, run, search_step).get("chunks", [])
    answer = summarize_with_llm(query, chunks)
    now = datetime.now(UTC)
    report = {
        "report_id": f"report_{uuid4().hex}",
        "query": query,
        "answer": answer,
        "source_chunks": trim_source_chunks(chunks),
        "created_at": now,
    }
    db.reports.insert_one(report)
    return report


def verify_step_output(step: WorkflowStep) -> None:
    if step.status != "succeeded":
        raise ValueError("Step did not succeed")
    if not step.output:
        raise ValueError("Step returned no output")
    if step.kind == "llm_plan":
        questions = step.output.get("questions") or []
        if questions and not step.output.get("steps"):
            raise ValueError("Planner requested input before execution")
        if not step.output.get("steps"):
            raise ValueError("Planner returned no executable steps")


def build_final_result(run: WorkflowRun) -> dict[str, Any]:
    final_step = next((step for step in reversed(run.steps) if step.kind == "llm_review"), None)
    if final_step and final_step.output.get("final_answer"):
        return {
            "answer": final_step.output["final_answer"],
            "review": final_step.output,
            "step_count": len(run.steps),
        }
    for step in reversed(run.steps):
        if step.output.get("answer") or step.output.get("summary"):
            return {"answer": step.output.get("answer") or step.output.get("summary"), "step_count": len(run.steps)}
    return {"answer": "Workflow completed.", "step_count": len(run.steps)}


def workflow_text_context(run: WorkflowRun, include_outputs: bool = False) -> str:
    parts = []
    if run.input_data.get("text"):
        parts.append(str(run.input_data["text"]))
    for chunk in last_search_chunks(run):
        parts.append(str(chunk.get("text", "")))
    if include_outputs:
        for step in run.steps:
            if step.output and step.kind != "llm_plan":
                parts.append(f"{step.name}: {step.output}")
    return "\n\n".join(part for part in parts if part).strip()


def last_search_chunks(run: WorkflowRun) -> list[dict[str, Any]]:
    for step in reversed(run.steps):
        chunks = step.output.get("chunks")
        if isinstance(chunks, list):
            return chunks
    return []


def latest_answer_text(run: WorkflowRun) -> str:
    for step in reversed(run.steps):
        for key in ("final_answer", "answer", "summary"):
            value = step.output.get(key)
            if value:
                return str(value)
    return ""


def trim_source_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "chunk_id": chunk.get("chunk_id"),
            "document_id": chunk.get("document_id"),
            "topic_id": chunk.get("topic_id"),
            "topic": chunk.get("topic"),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "keywords": chunk.get("keywords", []),
            "metadata": chunk.get("metadata", {}),
        }
        for chunk in chunks
    ]


def fallback_facts(text: str) -> list[dict[str, str]]:
    facts = []
    for index, sentence in enumerate(split_sentences(text)[:8], start=1):
        facts.append({"label": f"fact_{index}", "value": sentence, "evidence": sentence[:200]})
    return facts


def fallback_summary_text(text: str) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return "사용 가능한 결과가 없습니다."
    return normalized[:1200]


def split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    sentences = []
    for part in normalized.replace("다.", "다.|").replace(". ", ".|").split("|"):
        clean = part.strip()
        if clean:
            sentences.append(clean[:500])
    return sentences


def has_execution_plan(run: WorkflowRun) -> bool:
    return any(step.kind != "llm_plan" for step in run.steps)
