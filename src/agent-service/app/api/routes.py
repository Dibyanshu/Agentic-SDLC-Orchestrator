from fastapi import APIRouter, HTTPException

from app.graph.runner import start_workflow, handle_hitl_action
from app.schemas.contracts import (
    HealthResponse,
    HitlActionRequest,
    StartWorkflowRequest,
    WorkflowResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="agent-service")


@router.post("/workflow/start", response_model=WorkflowResponse)
def workflow_start(request: StartWorkflowRequest) -> WorkflowResponse:
    if not request.project_id.strip() or not request.input.strip():
        raise HTTPException(status_code=400, detail="project_id and input are required")

    return start_workflow(request)


@router.post("/workflow/hitl", response_model=WorkflowResponse)
def workflow_hitl(request: HitlActionRequest) -> WorkflowResponse:
    if request.action not in {"approve", "edit", "regenerate"}:
        raise HTTPException(status_code=400, detail="action must be approve, edit, or regenerate")

    return handle_hitl_action(request)

