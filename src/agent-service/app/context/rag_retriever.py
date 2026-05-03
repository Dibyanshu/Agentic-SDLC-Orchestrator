from typing import Any

from app.context.embeddings import embed_text
from app.context.rag_ingestion import get_rag_collection


def retrieve_rag_chunks(project_id: str, stage: str, top_k: int = 5) -> list[dict[str, object]]:
    try:
        collection = get_rag_collection()
        result = collection.query(
            query_embeddings=[embed_text(stage)],
            n_results=top_k,
            where={"project_id": project_id},
        )
    except Exception:
        return []

    documents = _first_result(result.get("documents"))
    distances = _first_result(result.get("distances"))
    metadatas = _first_result(result.get("metadatas"))
    ids = _first_result(result.get("ids"))

    chunks: list[dict[str, object]] = []
    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        distance = float(distances[index]) if index < len(distances) else 0.0
        chunk_id = str(ids[index]) if index < len(ids) else str(metadata.get("source_id", "unknown"))
        chunks.append(
            {
                "chunk_id": chunk_id,
                "content": document,
                "relevance_score": max(0.0, 1.0 - distance),
                "source_type": metadata.get("source_type", "txt"),
                "source_id": metadata.get("source_id"),
                "file_name": metadata.get("file_name"),
                "chunk_index": metadata.get("chunk_index"),
            }
        )

    return chunks


def _first_result(value: Any) -> list[Any]:
    if not value:
        return []

    return value[0]
