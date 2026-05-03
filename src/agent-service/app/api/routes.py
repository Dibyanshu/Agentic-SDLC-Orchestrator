from fastapi import APIRouter, HTTPException

from app.graph.runner import (
    get_checkpoints,
    get_llm_logs,
    get_section,
    get_section_versions,
    get_sections,
    get_workflow_metrics,
    get_workflow_state,
    handle_hitl_action,
    resume_workflow,
    start_workflow,
    update_section,
    WorkflowValidationError,
)
from app.schemas.contracts import (
    CheckpointsResponse,
    HealthResponse,
    HitlActionRequest,
    LlmLogsResponse,
    SectionResponse,
    SectionVersionsResponse,
    SectionsResponse,
    ResumeWorkflowRequest,
    StartWorkflowRequest,
    UpdateSectionRequest,
    WorkflowMetricsResponse,
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


@router.post("/workflow/resume", response_model=WorkflowResponse)
def workflow_resume(request: ResumeWorkflowRequest) -> WorkflowResponse:
    if not request.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    try:
        return resume_workflow(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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


@router.get(
    "/sections/{project_id}/{artifact_type}/{section_name}",
    response_model=SectionResponse,
)
def project_section(
    project_id: str,
    artifact_type: str,
    section_name: str,
) -> SectionResponse:
    response = get_section(project_id, artifact_type, section_name)
    if response is None:
        raise HTTPException(status_code=404, detail="section was not found")

    return response


@router.put(
    "/sections/{project_id}/{artifact_type}/{section_name}",
    response_model=SectionResponse,
)
def project_section_update(
    project_id: str,
    artifact_type: str,
    section_name: str,
    request: UpdateSectionRequest,
) -> SectionResponse:
    response = update_section(project_id, artifact_type, section_name, request.content)
    if response is None:
        raise HTTPException(status_code=404, detail="section was not found")

    return response


@router.get(
    "/sections/{project_id}/{artifact_type}/{section_name}/versions",
    response_model=SectionVersionsResponse,
)
def project_section_versions(
    project_id: str,
    artifact_type: str,
    section_name: str,
) -> SectionVersionsResponse:
    response = get_section_versions(project_id, artifact_type, section_name)
    if response is None:
        raise HTTPException(status_code=404, detail="section was not found")

    return response


@router.get("/checkpoints/{project_id}", response_model=CheckpointsResponse)
def project_checkpoints(project_id: str) -> CheckpointsResponse:
    response = get_checkpoints(project_id)
    if response is None:
        raise HTTPException(status_code=404, detail="checkpoints were not found")

    return response


@router.get("/logs/llm/{project_id}", response_model=LlmLogsResponse)
def project_llm_logs(project_id: str) -> LlmLogsResponse:
    return get_llm_logs(project_id)


@router.get("/metrics/workflow/{project_id}", response_model=WorkflowMetricsResponse)
def workflow_metrics(project_id: str) -> WorkflowMetricsResponse:
    return get_workflow_metrics(project_id)


@router.post("/workflow/hitl", response_model=WorkflowResponse)
def workflow_hitl(request: HitlActionRequest) -> WorkflowResponse:
    if request.action not in {"approve", "edit", "regenerate"}:
        raise HTTPException(status_code=400, detail="action must be approve, edit, or regenerate")

    try:
        return handle_hitl_action(request)
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
