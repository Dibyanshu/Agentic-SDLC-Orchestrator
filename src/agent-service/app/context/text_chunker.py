CHUNK_SIZE = 1_200
CHUNK_OVERLAP = 160


def chunk_text(text: str) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
    collapsed = "\n".join(paragraphs) if paragraphs else text
    chunks: list[str] = []
    cursor = 0

    while cursor < len(collapsed):
        end = min(cursor + CHUNK_SIZE, len(collapsed))
        chunks.append(collapsed[cursor:end].strip())
        if end == len(collapsed):
            break
        cursor = max(end - CHUNK_OVERLAP, cursor + 1)

    return chunks
