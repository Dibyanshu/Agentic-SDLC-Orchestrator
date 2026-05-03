import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from app.context.chroma_client import get_collection
from app.context.document_parser import parse_source_content
from app.context.embeddings import embed_text
from app.context.text_chunker import chunk_text
from app.persistence.mysql_client import MysqlClient

MAX_SOURCE_CHARS = 200_000


class RagSourceStore:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def save_source(
        self,
        project_id: str,
        file_name: str,
        source_type: str,
        content_hash: str,
        chunk_count: int,
    ) -> dict[str, Any]:
        self._ensure_table()
        source_id = f"rag_{uuid.uuid4().hex[:16]}"
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO rag_sources (
                          id, project_id, file_name, source_type, content_hash, chunk_count
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            source_id,
                            project_id,
                            file_name,
                            source_type,
                            content_hash,
                            chunk_count,
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return {
            "id": source_id,
            "project_id": project_id,
            "file_name": file_name,
            "source_type": source_type,
            "content_hash": content_hash,
            "chunk_count": chunk_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def list_sources(self, project_id: str) -> list[dict[str, Any]]:
        self._ensure_table()
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, project_id, file_name, source_type, content_hash, chunk_count, created_at
                    FROM rag_sources
                    WHERE project_id = %s
                    ORDER BY created_at DESC, id DESC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "project_id": row["project_id"],
                "file_name": row["file_name"],
                "source_type": row["source_type"],
                "content_hash": row["content_hash"],
                "chunk_count": row["chunk_count"],
                "created_at": row["created_at"].isoformat(),
            }
            for row in rows
        ]

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        self._ensure_table()
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, project_id, file_name, source_type, content_hash, chunk_count, created_at
                    FROM rag_sources
                    WHERE id = %s
                    """,
                    (source_id,),
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "project_id": row["project_id"],
            "file_name": row["file_name"],
            "source_type": row["source_type"],
            "content_hash": row["content_hash"],
            "chunk_count": row["chunk_count"],
            "created_at": row["created_at"].isoformat(),
        }

    def delete_source(self, source_id: str) -> bool:
        self._ensure_table()
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM rag_sources
                        WHERE id = %s
                        """,
                        (source_id,),
                    )
                    deleted = cursor.rowcount > 0
                connection.commit()
                return deleted
            except Exception:
                connection.rollback()
                raise

    def _ensure_table(self) -> None:
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS rag_sources (
                          id VARCHAR(50) PRIMARY KEY,
                          project_id VARCHAR(50) NOT NULL,
                          file_name VARCHAR(255) NOT NULL,
                          source_type VARCHAR(50) NOT NULL,
                          content_hash VARCHAR(64) NOT NULL,
                          chunk_count INT NOT NULL DEFAULT 0,
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          CONSTRAINT fk_rag_sources_projects FOREIGN KEY (project_id) REFERENCES projects(id)
                        )
                        """
                    )
                    cursor.execute(
                        """
                        CREATE INDEX idx_rag_sources_project_id ON rag_sources(project_id)
                        """
                    )
            except Exception as exc:
                if "Duplicate key name" not in str(exc):
                    connection.rollback()
                    raise
            else:
                connection.commit()


def ingest_source(project_id: str, file_name: str, source_type: str, content: str) -> dict[str, Any]:
    normalized_type = source_type.strip().lower()
    if normalized_type not in {"txt", "pdf", "docx"}:
        raise ValueError("sourceType must be txt, pdf, or docx")

    try:
        parsed_content = parse_source_content(normalized_type, content)
    except Exception as exc:
        raise ValueError(f"{normalized_type} source could not be parsed") from exc

    normalized = parsed_content.strip()
    if not normalized:
        raise ValueError("source content could not be parsed into text")

    if len(normalized) > MAX_SOURCE_CHARS:
        raise ValueError(f"parsed source content must be {MAX_SOURCE_CHARS} characters or fewer")

    chunks = chunk_text(normalized)
    source_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    source = RagSourceStore().save_source(
        project_id=project_id,
        file_name=file_name,
        source_type=normalized_type,
        content_hash=source_hash,
        chunk_count=len(chunks),
    )

    collection = get_collection()
    ids = [f"{source['id']}:{index}" for index in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=[embed_text(chunk) for chunk in chunks],
        metadatas=[
            {
                "project_id": project_id,
                "source_id": source["id"],
                "source_type": normalized_type,
                "file_name": file_name,
                "chunk_index": index,
            }
            for index in range(len(chunks))
        ],
    )

    return source


def ingest_txt_source(project_id: str, file_name: str, content: str) -> dict[str, Any]:
    return ingest_source(project_id, file_name, "txt", content)


def list_rag_sources(project_id: str) -> list[dict[str, Any]]:
    return RagSourceStore().list_sources(project_id)


def delete_rag_source(source_id: str) -> dict[str, Any] | None:
    store = RagSourceStore()
    source = store.get_source(source_id)
    if source is None:
        return None

    collection = get_collection()
    collection.delete(where={"source_id": source_id})
    store.delete_source(source_id)
    return source


def get_rag_collection():
    return get_collection()
