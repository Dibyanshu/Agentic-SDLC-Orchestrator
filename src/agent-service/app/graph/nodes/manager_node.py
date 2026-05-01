from app.regeneration.regeneration_planner import plan_regeneration
from app.schemas.state import AgentState


def manager_node(state: AgentState) -> AgentState:
    state["current_node"] = "manager_node"
    state.setdefault("execution_history", []).append("manager_node")

    updated_section = state.get("updated_section")
    if updated_section:
        state["execution_plan"] = plan_regeneration(
            updated_section,
            state.get("regeneration_mode", "single"),
        )
    else:
        state["execution_plan"] = ["pm_node"]

    return state

