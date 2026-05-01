from app.agents.ba_agent import generate_ba
from app.schemas.state import AgentState


def ba_node(state: AgentState) -> AgentState:
    state["current_node"] = "ba_node"
    state.setdefault("execution_history", []).append("ba_node")

    artifacts = state.setdefault("artifacts", {})
    artifacts["BA"] = generate_ba(artifacts.get("PRD", {}))
    state["status"] = "running"
    return state

