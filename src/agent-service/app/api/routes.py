from fastapi import APIRouter, HTTPException

from app.graph.runner import (
    get_checkpoints,
    get_sections,
    get_workflow_state,
    handle_hitl_action,
    start_workflow,
)
from app.schemas.contracts import (
    CheckpointsResponse,
    HealthResponse,
    HitlActionRequest,
    SectionsResponse,
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


@router.get("/workflow/{project_id}/state", response_model=WorkflowResponse)
def workflow_state(project_id: str) -> WorkflowResponse:
    response = get_workflow_state(project_id)
    if response is None:
        raise HTTPException(status_code=404, detail="workflow state was not found")

    return response


@router.get("/sections/{project_id}", response_model=SectionsResponse)
def project_sections(project_id: str) -> SectionsResponse:
    response = get_sections(project_id)
    if response is None:
        raise HTTPException(status_code=404, detail="sections were not found")

    return response


@router.get("/checkpoints/{project_id}", response_model=CheckpointsResponse)
def project_checkpoints(project_id: str) -> CheckpointsResponse:
    response = get_checkpoints(project_id)
    if response is None:
        raise HTTPException(status_code=404, detail="checkpoints were not found")

    return response


@router.post("/workflow/hitl", response_model=WorkflowResponse)
def workflow_hitl(request: HitlActionRequest) -> WorkflowResponse:
    if request.action not in {"approve", "edit", "regenerate"}:
        raise HTTPException(status_code=400, detail="action must be approve, edit, or regenerate")

    try:
        return handle_hitl_action(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
