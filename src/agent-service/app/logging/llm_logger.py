import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.persistence.mysql_client import MysqlClient


class LlmLogger:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def log(self, payload: dict[str, Any]) -> int:
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO llm_logs (
                          project_id,
                          artifact_id,
                          section_id,
                          node_name,
                          agent_name,
                          model_name,
                          prompt_template_version,
                          system_prompt,
                          user_prompt,
                          context_payload,
                          response_text,
                          response_format,
                          status,
                          error_message,
                          input_tokens,
                          output_tokens,
                          total_tokens,
                          estimated_cost,
                          latency_ms,
                          cache_hit,
                          cache_key,
                          start_time,
                          end_time
                        )
                        VALUES (
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, CAST(%s AS JSON),
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            payload["project_id"],
                            payload.get("artifact_id"),
                            payload.get("section_id"),
                            payload["node_name"],
                            payload["agent_name"],
                            payload["model_name"],
                            payload.get("prompt_template_version"),
                            payload["system_prompt"],
                            payload["user_prompt"],
                            json.dumps(payload.get("context_payload", {})),
                            payload.get("response_text"),
                            payload.get("response_format", "json"),
                            payload["status"],
                            payload.get("error_message"),
                            payload.get("input_tokens", 0),
                            payload.get("output_tokens", 0),
                            payload.get("total_tokens", 0),
                            Decimal(str(payload.get("estimated_cost", 0))),
                            payload.get("latency_ms", 0),
                            payload.get("cache_hit", False),
                            payload.get("cache_key"),
                            payload.get("start_time"),
                            payload.get("end_time"),
                        ),
                    )
                    log_id = int(cursor.lastrowid)
                connection.commit()
                return log_id
            except Exception:
                connection.rollback()
                raise

    def list_by_project(self, project_id: str) -> list[dict[str, Any]]:
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                      id,
                      project_id,
                      artifact_id,
                      section_id,
                      node_name,
                      agent_name,
                      model_name,
                      prompt_template_version,
                      system_prompt,
                      user_prompt,
                      context_payload,
                      response_text,
                      response_format,
                      status,
                      error_message,
                      input_tokens,
                      output_tokens,
                      total_tokens,
                      estimated_cost,
                      latency_ms,
                      cache_hit,
                      cache_key,
                      start_time,
                      end_time,
                      created_at
                    FROM llm_logs
                    WHERE project_id = %s
                    ORDER BY id DESC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        return [_to_response(row) for row in rows]


def log_llm_call(payload: dict[str, Any]) -> int:
    return LlmLogger().log(payload)


def _to_response(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "artifact_id": row["artifact_id"],
        "section_id": row["section_id"],
        "node_name": row["node_name"],
        "agent_name": row["agent_name"],
        "model_name": row["model_name"],
        "prompt_template_version": row["prompt_template_version"],
        "system_prompt": row["system_prompt"],
        "user_prompt": row["user_prompt"],
        "context_payload": _decode_json(row["context_payload"]),
        "response_text": row["response_text"],
        "response_format": row["response_format"],
        "status": row["status"],
        "error_message": row["error_message"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
        "total_tokens": row["total_tokens"],
        "estimated_cost": str(row["estimated_cost"]),
        "latency_ms": row["latency_ms"],
        "cache_hit": bool(row["cache_hit"]),
        "cache_key": row["cache_key"],
        "start_time": _format_datetime(row["start_time"]),
        "end_time": _format_datetime(row["end_time"]),
        "created_at": _format_datetime(row["created_at"]),
    }


def _decode_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    return json.loads(value)


def _format_datetime(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()

    return str(value)
