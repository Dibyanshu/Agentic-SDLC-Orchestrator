from app.graph.nodes.ba_node import ba_node
from app.graph.nodes.architect_node import architect_node
from app.graph.nodes.hitl_node import hitl_node
from app.graph.nodes.manager_node import manager_node
from app.graph.nodes.pm_node import pm_node
from app.persistence.checkpoint_store import MySqlCheckpointStore
from app.persistence.section_store import SectionStore
from app.logging.llm_logger import LlmLogger
from app.schemas.contracts import (
    CheckpointResponse,
    CheckpointsResponse,
    HitlActionRequest,
    SectionResponse,
    SectionVersionResponse,
    SectionVersionsResponse,
    SectionsResponse,
    StartWorkflowRequest,
    ResumeWorkflowRequest,
    WorkflowResponse,
    LlmLogResponse,
    LlmLogsResponse,
)
from app.schemas.state import AgentState

_STATE_STORE: dict[str, AgentState] = {}
_CHECKPOINT_STORE = MySqlCheckpointStore()
_SECTION_STORE = SectionStore()
_LLM_LOGGER = LlmLogger()


def start_workflow(request: StartWorkflowRequest) -> WorkflowResponse:
    state: AgentState = {
        "project_id": request.project_id,
        "input": request.input,
        "current_node": "manager_node",
        "artifacts": {},
        "updated_section": None,
        "regeneration_mode": "none",
        "context_cache": [],
        "execution_history": [],
        "execution_plan": [],
        "status": "running",
    }

    state = manager_node(state)
    _save_checkpoint(state)
    state = pm_node(state)
    _save_artifact(state, "PRD", "pm_node")
    _save_checkpoint(state)
    state = hitl_node(state)
    _save_checkpoint(state)
    _STATE_STORE[request.project_id] = state
    return _to_response(state)


def resume_workflow(request: ResumeWorkflowRequest) -> WorkflowResponse:
    state = _CHECKPOINT_STORE.get(request.project_id)
    if state is None:
        raise ValueError("workflow checkpoint was not found")

    status = state.get("status")
    current_node = state.get("current_node")
    if status in {"paused_for_hitl", "completed"} or current_node in {"hitl_node", "end"}:
        _STATE_STORE[request.project_id] = state
        return _to_response(state)

    state = _continue_running_state(state)
    _STATE_STORE[request.project_id] = state
    return _to_response(state)


def handle_hitl_action(request: HitlActionRequest) -> WorkflowResponse:
    state = _STATE_STORE.get(request.project_id)
    if state is None:
        state = _CHECKPOINT_STORE.get(request.project_id)

    if state is None:
        raise ValueError("workflow state was not found")

    if request.action == "edit":
        _apply_section_edit(state, request)
        _SECTION_STORE.save_refinement_log(
            request.project_id,
            request.section,
            "edit",
            request.content,
        )
        state["status"] = "paused_for_hitl"
        artifact_type, _, section_name = (request.section or "").partition(".")
        if artifact_type and section_name:
            artifact = state.get("artifacts", {}).get(artifact_type, {})
            if section_name in artifact:
                _SECTION_STORE.save_artifact_sections(
                    state["project_id"],
                    artifact_type,
                    {section_name: artifact[section_name]},
                    "hitl_edit",
                )
        _save_checkpoint(state)
    elif request.action == "regenerate":
        state["updated_section"] = request.section
        state["regeneration_mode"] = request.mode or "single"
        _SECTION_STORE.save_refinement_log(
            request.project_id,
            request.section,
            f"regenerate:{state['regeneration_mode']}",
            None,
        )
        state = manager_node(state)
        _save_checkpoint(state)
        state = _run_execution_plan(state)
        state = hitl_node(state)
        _save_checkpoint(state)
    elif request.action == "approve":
        _SECTION_STORE.save_refinement_log(
            request.project_id,
            None,
            "approve",
            None,
        )
        state = _advance_after_approval(state)
        _save_checkpoint(state)

    _STATE_STORE[request.project_id] = state
    return _to_response(state)


def get_workflow_state(project_id: str) -> WorkflowResponse | None:
    state = _STATE_STORE.get(project_id)
    if state is None:
        state = _CHECKPOINT_STORE.get(project_id)
        if state is None:
            return None
        _STATE_STORE[project_id] = state

    return _to_response(state)


def get_sections(project_id: str) -> SectionsResponse | None:
    state = _STATE_STORE.get(project_id)
    persisted_sections = _SECTION_STORE.get_sections(project_id)
    if persisted_sections:
        sections = [
            SectionResponse(
                id=row["id"],
                artifact_type=row["artifact_type"],
                section_name=row["section_name"],
                version=row["version"],
                content=row["content"],
            )
            for row in persisted_sections
        ]
        return SectionsResponse(project_id=project_id, sections=sections)

    if state is None:
        return None

    sections: list[SectionResponse] = []
    for artifact_type, artifact_sections in state.get("artifacts", {}).items():
        for section_name, content in artifact_sections.items():
            sections.append(
                SectionResponse(
                    artifact_type=artifact_type,
                    section_name=section_name,
                    content=content,
                )
            )

    return SectionsResponse(project_id=project_id, sections=sections)


def get_section(
    project_id: str,
    artifact_type: str,
    section_name: str,
) -> SectionResponse | None:
    row = _SECTION_STORE.get_section(project_id, artifact_type, section_name)
    if row is None:
        return None

    return SectionResponse(
        id=row["id"],
        artifact_type=row["artifact_type"],
        section_name=row["section_name"],
        version=row["version"],
        content=row["content"],
    )


def update_section(
    project_id: str,
    artifact_type: str,
    section_name: str,
    content: object,
) -> SectionResponse | None:
    row = _SECTION_STORE.update_section(
        project_id,
        artifact_type,
        section_name,
        content,
        "section_update",
    )
    if row is None:
        return None

    state = _STATE_STORE.get(project_id) or _CHECKPOINT_STORE.get(project_id)
    if state is not None:
        artifacts = state.setdefault("artifacts", {})
        artifact = artifacts.setdefault(artifact_type, {})
        artifact[section_name] = content
        state["updated_section"] = f"{artifact_type}.{section_name}"
        state.setdefault("execution_history", []).append(
            f"section_update:{artifact_type}.{section_name}"
        )
        _save_checkpoint(state)
        _STATE_STORE[project_id] = state

    return SectionResponse(
        id=row["id"],
        artifact_type=row["artifact_type"],
        section_name=row["section_name"],
        version=row["version"],
        content=row["content"],
    )


def get_section_versions(
    project_id: str,
    artifact_type: str,
    section_name: str,
) -> SectionVersionsResponse | None:
    rows = _SECTION_STORE.get_section_versions(project_id, artifact_type, section_name)
    if rows is None:
        return None

    versions = [
        SectionVersionResponse(
            id=row["id"],
            section_id=row["section_id"],
            version=row["version"],
            content=row["content"],
            change_reason=row["change_reason"],
            created_at=row["created_at"],
        )
        for row in rows
    ]

    return SectionVersionsResponse(
        project_id=project_id,
        artifact_type=artifact_type,
        section_name=section_name,
        versions=versions,
    )


def get_checkpoints(project_id: str) -> CheckpointsResponse | None:
    rows = _CHECKPOINT_STORE.list(project_id)
    if not rows:
        return None

    checkpoints = [
        CheckpointResponse(
            id=row["id"],
            project_id=row["project_id"],
            current_node=row["current_node"],
            status=row["status"],
            graph_state=row["graph_state"],
            created_at=row["created_at"],
        )
        for row in rows
    ]

    return CheckpointsResponse(project_id=project_id, checkpoints=checkpoints)


def get_llm_logs(project_id: str) -> LlmLogsResponse:
    rows = _LLM_LOGGER.list_by_project(project_id)
    logs = [
        LlmLogResponse(
            id=row["id"],
            project_id=row["project_id"],
            artifact_id=row["artifact_id"],
            section_id=row["section_id"],
            node_name=row["node_name"],
            agent_name=row["agent_name"],
            model_name=row["model_name"],
            prompt_template_version=row["prompt_template_version"],
            system_prompt=row["system_prompt"],
            user_prompt=row["user_prompt"],
            context_payload=row["context_payload"],
            response_text=row["response_text"],
            response_format=row["response_format"],
            status=row["status"],
            error_message=row["error_message"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            total_tokens=row["total_tokens"],
            estimated_cost=row["estimated_cost"],
            latency_ms=row["latency_ms"],
            cache_hit=row["cache_hit"],
            cache_key=row["cache_key"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return LlmLogsResponse(project_id=project_id, logs=logs)


def _apply_section_edit(state: AgentState, request: HitlActionRequest) -> None:
    if not request.section or request.content is None:
        return

    artifact_type, _, section_name = request.section.partition(".")
    if not artifact_type or not section_name:
        return

    artifacts = state.setdefault("artifacts", {})
    artifact = artifacts.setdefault(artifact_type, {})
    artifact[section_name] = request.content
    state["updated_section"] = request.section
    state.setdefault("execution_history", []).append(f"edit:{request.section}")


def _advance_after_approval(state: AgentState) -> AgentState:
    history = state.setdefault("execution_history", [])
    artifacts = state.setdefault("artifacts", {})

    if "PRD" in artifacts and "BA" not in artifacts:
        state["status"] = "running"
        state = ba_node(state)
        _save_artifact(state, "BA", "ba_node")
        return hitl_node(state)

    if "BA" in artifacts and "ARCH" not in artifacts:
        state["status"] = "running"
        state = architect_node(state)
        _save_artifact(state, "ARCH", "architect_node")
        return hitl_node(state)

    state["status"] = "completed"
    state["current_node"] = "end"
    history.append("workflow:completed")
    return state


def _run_execution_plan(state: AgentState) -> AgentState:
    plan = state.get("execution_plan") or ["pm_node"]

    for node_name in plan:
        if node_name == "pm_node":
            state = pm_node(state)
            _save_artifact(state, "PRD", node_name)
        elif node_name == "ba_node":
            state = ba_node(state)
            _save_artifact(state, "BA", node_name)
        elif node_name == "architect_node":
            state = architect_node(state)
            _save_artifact(state, "ARCH", node_name)
        _save_checkpoint(state)

    return state


def _continue_running_state(state: AgentState) -> AgentState:
    current_node = state.get("current_node")

    if current_node == "manager_node":
        state = _run_execution_plan(state)
        state = hitl_node(state)
        _save_checkpoint(state)
        return state

    if current_node == "pm_node":
        _save_artifact(state, "PRD", "resume:pm_node")
        state = hitl_node(state)
        _save_checkpoint(state)
        return state

    if current_node == "ba_node":
        _save_artifact(state, "BA", "resume:ba_node")
        state = hitl_node(state)
        _save_checkpoint(state)
        return state

    if current_node == "architect_node":
        _save_artifact(state, "ARCH", "resume:architect_node")
        state = hitl_node(state)
        _save_checkpoint(state)
        return state

    return state


def _save_artifact(state: AgentState, artifact_type: str, change_reason: str) -> None:
    artifact = state.get("artifacts", {}).get(artifact_type)
    if artifact:
        _SECTION_STORE.save_artifact_sections(
            state["project_id"],
            artifact_type,
            artifact,
            change_reason,
        )


def _save_checkpoint(state: AgentState) -> None:
    _CHECKPOINT_STORE.save(state["project_id"], state)


def _to_response(state: AgentState) -> WorkflowResponse:
    return WorkflowResponse(
        project_id=state["project_id"],
        status=state.get("status", "unknown"),
        current_node=state.get("current_node", "unknown"),
        artifacts=state.get("artifacts", {}),
    )
