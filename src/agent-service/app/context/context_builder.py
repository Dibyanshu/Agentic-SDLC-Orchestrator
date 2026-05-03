from app.context.rag_retriever import retrieve_rag_chunks


def build_context(stage: str, artifacts: dict[str, object], project_id: str | None = None) -> dict[str, object]:
    rag_chunks = retrieve_rag_chunks(project_id, stage, top_k=5)[:3] if project_id else []
    return {
        "stage": stage,
        "summary": artifacts,
        "rag_chunks": rag_chunks,
        "constraints": ["max_context_chunks=3"],
    }
