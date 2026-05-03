import json
import uuid
from typing import Any

from app.persistence.mysql_client import MysqlClient


class SectionStore:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def save_artifact_sections(
        self,
        project_id: str,
        artifact_type: str,
        sections: dict[str, Any],
        change_reason: str,
    ) -> None:
        artifact_id = self._ensure_artifact(project_id, artifact_type)

        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    for section_name, content in sections.items():
                        section_id = self._find_section_id(cursor, artifact_id, section_name)
                        content_json = json.dumps(content)

                        if section_id is None:
                            section_id = uuid.uuid4().hex
                            cursor.execute(
                                """
                                INSERT INTO sections (id, artifact_id, section_name, content, version)
                                VALUES (%s, %s, %s, CAST(%s AS JSON), 1)
                                """,
                                (section_id, artifact_id, section_name, content_json),
                            )
                            cursor.execute(
                                """
                                INSERT INTO section_versions (section_id, version, content, change_reason)
                                VALUES (%s, 1, CAST(%s AS JSON), %s)
                                """,
                                (section_id, content_json, change_reason),
                            )
                            continue

                        cursor.execute(
                            """
                            SELECT version, content
                            FROM sections
                            WHERE id = %s
                            FOR UPDATE
                            """,
                            (section_id,),
                        )
                        row = cursor.fetchone()
                        if _normalize_json(row["content"]) == _normalize_json(content):
                            continue

                        next_version = int(row["version"]) + 1

                        cursor.execute(
                            """
                            UPDATE sections
                            SET content = CAST(%s AS JSON), version = %s
                            WHERE id = %s
                            """,
                            (content_json, next_version, section_id),
                        )
                        cursor.execute(
                            """
                            INSERT INTO section_versions (section_id, version, content, change_reason)
                            VALUES (%s, %s, CAST(%s AS JSON), %s)
                            """,
                            (section_id, next_version, content_json, change_reason),
                        )

                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def save_refinement_log(
        self,
        project_id: str,
        qualified_section: str | None,
        action_type: str,
        user_input: str | None,
    ) -> None:
        section_id = None
        if qualified_section:
            artifact_type, _, section_name = qualified_section.partition(".")
            section_id = self._find_section_id_by_project(
                project_id,
                artifact_type,
                section_name,
            )

        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO refinement_logs (section_id, user_input, action_type)
                        VALUES (%s, %s, %s)
                        """,
                        (section_id, user_input, action_type),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def get_sections(self, project_id: str) -> list[dict[str, Any]]:
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT a.type AS artifact_type, s.section_name, s.content
                    FROM sections s
                    INNER JOIN artifacts a ON a.id = s.artifact_id
                    WHERE a.project_id = %s
                    ORDER BY a.created_at, s.created_at, s.section_name
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        return [
            {
                "artifact_type": row["artifact_type"],
                "section_name": row["section_name"],
                "content": _decode_json(row["content"]),
            }
            for row in rows
        ]

    def _ensure_artifact(self, project_id: str, artifact_type: str) -> str:
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id
                        FROM artifacts
                        WHERE project_id = %s AND type = %s
                        LIMIT 1
                        """,
                        (project_id, artifact_type),
                    )
                    row = cursor.fetchone()
                    if row:
                        return row["id"]

                    artifact_id = uuid.uuid4().hex
                    cursor.execute(
                        """
                        INSERT INTO artifacts (id, project_id, type)
                        VALUES (%s, %s, %s)
                        """,
                        (artifact_id, project_id, artifact_type),
                    )
                connection.commit()
                return artifact_id
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _find_section_id(cursor: Any, artifact_id: str, section_name: str) -> str | None:
        cursor.execute(
            """
            SELECT id
            FROM sections
            WHERE artifact_id = %s AND section_name = %s
            LIMIT 1
            """,
            (artifact_id, section_name),
        )
        row = cursor.fetchone()
        return row["id"] if row else None

    def _find_section_id_by_project(
        self,
        project_id: str,
        artifact_type: str,
        section_name: str,
    ) -> str | None:
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s.id
                    FROM sections s
                    INNER JOIN artifacts a ON a.id = s.artifact_id
                    WHERE a.project_id = %s AND a.type = %s AND s.section_name = %s
                    LIMIT 1
                    """,
                    (project_id, artifact_type, section_name),
                )
                row = cursor.fetchone()
                return row["id"] if row else None


def _decode_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _normalize_json(value: Any) -> str:
    return json.dumps(_decode_json(value), sort_keys=True, separators=(",", ":"))
