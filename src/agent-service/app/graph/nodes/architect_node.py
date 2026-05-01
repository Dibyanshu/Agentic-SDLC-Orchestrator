from app.agents.architect_agent import generate_architecture
from app.schemas.state import AgentState


def architect_node(state: AgentState) -> AgentState:
    state["current_node"] = "architect_node"
    state.setdefault("execution_history", []).append("architect_node")

    artifacts = state.setdefault("artifacts", {})
    artifacts["ARCH"] = generate_architecture(artifacts.get("BA", {}))
    state["status"] = "running"
    return state

