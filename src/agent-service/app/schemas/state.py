from typing import Any, Literal, TypedDict


RegenerationMode = Literal["none", "single", "cascade"]


class AgentState(TypedDict, total=False):
    project_id: str
    current_node: str
    input: str
    artifacts: dict[str, dict[str, Any]]
    updated_section: str | None
    regeneration_mode: RegenerationMode
    context_cache: list[dict[str, Any]]
    execution_history: list[str]
    execution_plan: list[str]
    refinement_counts: dict[str, int]
    status: str
