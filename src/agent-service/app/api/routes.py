from fastapi import APIRouter, HTTPException

from app.context.rag_ingestion import delete_rag_source, ingest_source, list_rag_sources
from app.llm.llm_client import LlmConfigurationError
from app.llm.settings import AgentLlmSettings
from app.llm.token_budget import TokenBudgetExceededError
from app.persistence.llm_settings_store import LlmSettingsStore
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
    LlmProvidersResponse,
    ProjectLlmSettingsResponse,
    ProjectLlmSettingsUpdateRequest,
    RagSourceCreateRequest,
    RagSourceResponse,
    RagSourcesResponse,
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
_LLM_SETTINGS = LlmSettingsStore()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="agent-service")


@router.post("/workflow/start", response_model=WorkflowResponse)
def workflow_start(request: StartWorkflowRequest) -> WorkflowResponse:
    if not request.project_id.strip() or not request.input.strip():
        raise HTTPException(status_code=400, detail="project_id and input are required")

    try:
        return start_workflow(request)
    except (LlmConfigurationError, TokenBudgetExceededError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/workflow/resume", response_model=WorkflowResponse)
def workflow_resume(request: ResumeWorkflowRequest) -> WorkflowResponse:
    if not request.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    try:
        return resume_workflow(request)
    except (LlmConfigurationError, TokenBudgetExceededError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@router.get("/llm/providers", response_model=LlmProvidersResponse)
def llm_providers() -> LlmProvidersResponse:
    return LlmProvidersResponse(providers=_LLM_SETTINGS.list_providers())


@router.get("/projects/{project_id}/llm-settings", response_model=ProjectLlmSettingsResponse)
def project_llm_settings(project_id: str) -> ProjectLlmSettingsResponse:
    settings = _LLM_SETTINGS.get_project_settings(project_id)
    return ProjectLlmSettingsResponse(projectId=project_id, agents=_to_llm_settings_response(settings))


@router.put("/projects/{project_id}/llm-settings", response_model=ProjectLlmSettingsResponse)
def project_llm_settings_update(
    project_id: str,
    request: ProjectLlmSettingsUpdateRequest,
) -> ProjectLlmSettingsResponse:
    try:
        settings = _LLM_SETTINGS.save_project_settings(
            project_id,
            {
                agent_name: AgentLlmSettings(
                    provider=agent_settings.provider,
                    model=agent_settings.model,
                    token_budget=agent_settings.token_budget,
                )
                for agent_name, agent_settings in request.agents.items()
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ProjectLlmSettingsResponse(projectId=project_id, agents=_to_llm_settings_response(settings))


@router.post("/rag/sources", response_model=RagSourceResponse)
def rag_source_create(request: RagSourceCreateRequest) -> RagSourceResponse:
    if not request.project_id.strip():
        raise HTTPException(status_code=400, detail="project_id is required")

    source_type = request.source_type.strip().lower()
    if source_type not in {"txt", "pdf", "docx"}:
        raise HTTPException(status_code=400, detail="sourceType must be txt, pdf, or docx")

    try:
        source = ingest_source(
            request.project_id,
            request.file_name.strip() or f"source.{source_type}",
            source_type,
            request.content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RagSourceResponse(**source)


@router.get("/rag/sources/{project_id}", response_model=RagSourcesResponse)
def rag_sources(project_id: str) -> RagSourcesResponse:
    return RagSourcesResponse(projectId=project_id, sources=list_rag_sources(project_id))


@router.delete("/rag/sources/{source_id}", status_code=204)
def rag_source_delete(source_id: str) -> None:
    source = delete_rag_source(source_id.strip())
    if source is None:
        raise HTTPException(status_code=404, detail="RAG source was not found")

    return None


@router.post("/workflow/hitl", response_model=WorkflowResponse)
def workflow_hitl(request: HitlActionRequest) -> WorkflowResponse:
    if request.action not in {"approve", "edit", "regenerate"}:
        raise HTTPException(status_code=400, detail="action must be approve, edit, or regenerate")

    try:
        return handle_hitl_action(request)
    except (LlmConfigurationError, TokenBudgetExceededError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _to_llm_settings_response(settings: dict[str, AgentLlmSettings]) -> dict[str, dict[str, object]]:
    return {
        agent_name: {
            "provider": agent_settings.provider,
            "model": agent_settings.model,
            "tokenBudget": agent_settings.token_budget,
        }
        for agent_name, agent_settings in settings.items()
    }
