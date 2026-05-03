from app.context.rag_retriever import retrieve_rag_chunks


def build_context(stage: str, artifacts: dict[str, object], project_id: str | None = None) -> dict[str, object]:
    rag_chunks = _dedupe_chunks(retrieve_rag_chunks(project_id, stage, top_k=5))[:3] if project_id else []
    return {
        "stage": stage,
        "summary": artifacts,
        "rag_chunks": rag_chunks,
        "constraints": ["max_context_chunks=3"],
    }


def _dedupe_chunks(chunks: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    deduped: list[dict[str, object]] = []
    for chunk in chunks:
        content = str(chunk.get("content", "")).strip()
        key = content.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(chunk)

    return deduped
