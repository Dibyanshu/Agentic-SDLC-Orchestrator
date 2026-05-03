import json

from app.persistence.mysql_client import MysqlClient
from app.schemas.state import AgentState


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self._states: dict[str, AgentState] = {}

    def save(self, project_id: str, state: AgentState) -> None:
        self._states[project_id] = state

    def get(self, project_id: str) -> AgentState | None:
        return self._states.get(project_id)


class MySqlCheckpointStore:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def save(self, project_id: str, state: AgentState) -> None:
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO checkpoints (project_id, graph_state, current_node, status)
                        VALUES (%s, CAST(%s AS JSON), %s, %s)
                        """,
                        (
                            project_id,
                            json.dumps(state),
                            state.get("current_node", "unknown"),
                            state.get("status", "unknown"),
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def get(self, project_id: str) -> AgentState | None:
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT graph_state
                    FROM checkpoints
                    WHERE project_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (project_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return None

        graph_state = row["graph_state"]
        if isinstance(graph_state, str):
            return json.loads(graph_state)

        return graph_state

    def list(self, project_id: str) -> list[dict]:
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, project_id, graph_state, current_node, status, created_at
                    FROM checkpoints
                    WHERE project_id = %s
                    ORDER BY id DESC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "project_id": row["project_id"],
                "graph_state": _decode_graph_state(row["graph_state"]),
                "current_node": row["current_node"],
                "status": row["status"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ]


def _decode_graph_state(value: object) -> AgentState:
    if isinstance(value, str):
        return json.loads(value)

    return value
