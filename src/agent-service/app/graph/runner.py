from app.graph.nodes.ba_node import ba_node
from app.graph.nodes.architect_node import architect_node
from app.graph.nodes.hitl_node import hitl_node
from app.graph.nodes.manager_node import manager_node
from app.graph.nodes.pm_node import pm_node
from app.persistence.checkpoint_store import MySqlCheckpointStore
from app.persistence.section_store import SectionStore
from app.schemas.contracts import (
    HitlActionRequest,
    SectionResponse,
    SectionsResponse,
    StartWorkflowRequest,
    WorkflowResponse,
)
from app.schemas.state import AgentState

_STATE_STORE: dict[str, AgentState] = {}
_CHECKPOINT_STORE = MySqlCheckpointStore()
_SECTION_STORE = SectionStore()


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
                artifact_type=row["artifact_type"],
                section_name=row["section_name"],
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
