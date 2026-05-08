from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database import get_database
from app.local_store import LocalDatabase
from app.schemas import WorkflowResumeRequest, WorkflowRun, WorkflowRunRequest
from app.services.workflow_engine import get_workflow_run, resume_workflow_run, start_workflow_run

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/runs", response_model=WorkflowRun)
def create_workflow_run(
    request: WorkflowRunRequest,
    db: Database | LocalDatabase = Depends(get_database),
) -> WorkflowRun:
    return start_workflow_run(db, request)


@router.get("/runs/{run_id}", response_model=WorkflowRun)
def read_workflow_run(
    run_id: str,
    db: Database | LocalDatabase = Depends(get_database),
) -> WorkflowRun:
    run = get_workflow_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="워크플로우 실행을 찾을 수 없습니다.")
    return run


@router.post("/runs/{run_id}/resume", response_model=WorkflowRun)
def resume_run(
    run_id: str,
    request: WorkflowResumeRequest | None = None,
    db: Database | LocalDatabase = Depends(get_database),
) -> WorkflowRun:
    run = get_workflow_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="워크플로우 실행을 찾을 수 없습니다.")
    try:
        return resume_workflow_run(db, run, request or WorkflowResumeRequest())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
