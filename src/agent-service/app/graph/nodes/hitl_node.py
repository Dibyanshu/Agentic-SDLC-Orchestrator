from app.schemas.state import AgentState


def hitl_node(state: AgentState) -> AgentState:
    state["current_node"] = "hitl_node"
    state["status"] = "paused_for_hitl"
    state.setdefault("execution_history", []).append("hitl_node")
    return state

