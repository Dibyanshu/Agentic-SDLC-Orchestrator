import json
from typing import Any

from app.persistence.mysql_client import MysqlClient


class LlmCacheStore:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        self._ensure_table()
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT response_text, model_name, input_tokens, output_tokens
                    FROM llm_response_cache
                    WHERE cache_key = %s
                    """,
                    (cache_key,),
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return {
            "response_text": row["response_text"],
            "model_name": row["model_name"],
            "input_tokens": int(row["input_tokens"]),
            "output_tokens": int(row["output_tokens"]),
        }

    def set(
        self,
        *,
        cache_key: str,
        model_name: str,
        response_text: str,
        input_tokens: int,
        output_tokens: int,
        context_payload: dict[str, Any],
    ) -> None:
        self._ensure_table()
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO llm_response_cache (
                          cache_key, model_name, response_text, input_tokens, output_tokens, context_payload
                        )
                        VALUES (%s, %s, %s, %s, %s, CAST(%s AS JSON))
                        ON DUPLICATE KEY UPDATE
                          model_name = VALUES(model_name),
                          response_text = VALUES(response_text),
                          input_tokens = VALUES(input_tokens),
                          output_tokens = VALUES(output_tokens),
                          context_payload = VALUES(context_payload),
                          updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            cache_key,
                            model_name,
                            response_text,
                            input_tokens,
                            output_tokens,
                            json.dumps(context_payload),
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def _ensure_table(self) -> None:
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS llm_response_cache (
                          cache_key VARCHAR(128) PRIMARY KEY,
                          model_name VARCHAR(100) NOT NULL,
                          response_text LONGTEXT NOT NULL,
                          input_tokens INT NOT NULL DEFAULT 0,
                          output_tokens INT NOT NULL DEFAULT 0,
                          context_payload JSON NOT NULL,
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                        """
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
