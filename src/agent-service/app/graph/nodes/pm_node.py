from app.agents.pm_agent import generate_prd
from app.schemas.state import AgentState


def pm_node(state: AgentState) -> AgentState:
    state["current_node"] = "pm_node"
    state.setdefault("execution_history", []).append("pm_node")

    artifacts = state.setdefault("artifacts", {})
    artifacts["PRD"] = generate_prd(
        state.get("input", ""),
        state["project_id"],
        artifacts,
    )
    state["status"] = "running"
    return state
