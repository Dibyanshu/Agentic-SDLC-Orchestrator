from decimal import Decimal
from typing import Any

from app.persistence.mysql_client import MysqlClient


class MetricsStore:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def get_workflow_metrics(self, project_id: str) -> dict[str, Any]:
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                      COALESCE(SUM(input_tokens), 0) AS total_input_tokens,
                      COALESCE(SUM(output_tokens), 0) AS total_output_tokens,
                      COALESCE(SUM(total_tokens), 0) AS total_tokens,
                      COALESCE(SUM(estimated_cost), 0) AS estimated_cost,
                      COALESCE(SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END), 0) AS cache_hit_count,
                      COUNT(*) AS llm_call_count
                    FROM llm_logs
                    WHERE project_id = %s
                    """,
                    (project_id,),
                )
                totals = cursor.fetchone()

                cursor.execute(
                    """
                    SELECT
                      node_name,
                      COUNT(*) AS call_count,
                      COALESCE(SUM(latency_ms), 0) AS total_latency_ms,
                      COALESCE(AVG(latency_ms), 0) AS average_latency_ms
                    FROM llm_logs
                    WHERE project_id = %s
                    GROUP BY node_name
                    ORDER BY node_name
                    """,
                    (project_id,),
                )
                node_rows = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT COUNT(*) AS refinement_count
                    FROM refinement_logs r
                    INNER JOIN sections s ON s.id = r.section_id
                    INNER JOIN artifacts a ON a.id = s.artifact_id
                    WHERE a.project_id = %s
                      AND (r.action_type = 'edit' OR r.action_type LIKE 'regenerate%%')
                    """,
                    (project_id,),
                )
                refinement_row = cursor.fetchone()

        return {
            "project_id": project_id,
            "total_input_tokens": int(totals["total_input_tokens"]),
            "total_output_tokens": int(totals["total_output_tokens"]),
            "total_tokens": int(totals["total_tokens"]),
            "estimated_cost": _decimal_to_string(totals["estimated_cost"]),
            "cache_hit_count": int(totals["cache_hit_count"]),
            "llm_call_count": int(totals["llm_call_count"]),
            "refinement_count": int(refinement_row["refinement_count"]),
            "latency_by_node": [
                {
                    "node_name": row["node_name"],
                    "call_count": int(row["call_count"]),
                    "total_latency_ms": int(row["total_latency_ms"]),
                    "average_latency_ms": float(row["average_latency_ms"]),
                }
                for row in node_rows
            ],
        }


def _decimal_to_string(value: Any) -> str:
    if isinstance(value, Decimal):
        return str(value)

    return str(value or 0)
