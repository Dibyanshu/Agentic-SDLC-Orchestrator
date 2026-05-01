from app.graph.nodes.ba_node import ba_node
from app.graph.nodes.architect_node import architect_node
from app.graph.nodes.hitl_node import hitl_node
from app.graph.nodes.manager_node import manager_node
from app.graph.nodes.pm_node import pm_node
from app.schemas.contracts import HitlActionRequest, StartWorkflowRequest, WorkflowResponse
from app.schemas.state import AgentState

_STATE_STORE: dict[str, AgentState] = {}


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
    state = pm_node(state)
    state = hitl_node(state)
    _STATE_STORE[request.project_id] = state
    return _to_response(state)


def handle_hitl_action(request: HitlActionRequest) -> WorkflowResponse:
    state = _STATE_STORE.get(request.project_id)
    if state is None:
        state = {
            "project_id": request.project_id,
            "input": "",
            "current_node": "hitl_node",
            "artifacts": {},
            "updated_section": None,
            "regeneration_mode": "none",
            "context_cache": [],
            "execution_history": [],
            "execution_plan": [],
            "status": "paused_for_hitl",
        }

    if request.action == "edit":
        _apply_section_edit(state, request)
        state["status"] = "paused_for_hitl"
    elif request.action == "regenerate":
        state["updated_section"] = request.section
        state["regeneration_mode"] = request.mode or "single"
        state = manager_node(state)
        state = pm_node(state)
        state = hitl_node(state)
    elif request.action == "approve":
        state = _advance_after_approval(state)

    _STATE_STORE[request.project_id] = state
    return _to_response(state)


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
        return hitl_node(state)

    if "BA" in artifacts and "ARCH" not in artifacts:
        state["status"] = "running"
        state = architect_node(state)
        return hitl_node(state)

    state["status"] = "completed"
    state["current_node"] = "end"
    history.append("workflow:completed")
    return state


def _to_response(state: AgentState) -> WorkflowResponse:
    return WorkflowResponse(
        project_id=state["project_id"],
        status=state.get("status", "unknown"),
        current_node=state.get("current_node", "unknown"),
        artifacts=state.get("artifacts", {}),
    )
