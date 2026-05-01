def build_context(stage: str, artifacts: dict[str, object]) -> dict[str, object]:
    return {
        "stage": stage,
        "summary": artifacts,
        "rag_chunks": [],
        "constraints": ["max_context_chunks=3"],
    }

