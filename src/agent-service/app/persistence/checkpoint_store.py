from app.schemas.state import AgentState


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self._states: dict[str, AgentState] = {}

    def save(self, project_id: str, state: AgentState) -> None:
        self._states[project_id] = state

    def get(self, project_id: str) -> AgentState | None:
        return self._states.get(project_id)

