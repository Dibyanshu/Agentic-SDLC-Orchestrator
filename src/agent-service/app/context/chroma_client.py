import json
import os
from typing import Any
from urllib import request
from urllib.error import HTTPError

COLLECTION_NAME = "project_rag_chunks"


class ChromaCollection:
    def __init__(self, collection_id: str, base_url: str) -> None:
        self._collection_id = collection_id
        self._base_url = base_url.rstrip("/")

    def add(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        _post_json(
            f"{self._base_url}/api/v1/collections/{self._collection_id}/add",
            {
                "ids": ids,
                "documents": documents,
                "embeddings": embeddings,
                "metadatas": metadatas,
            },
        )

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
        where: dict[str, Any],
    ) -> dict[str, Any]:
        return _post_json(
            f"{self._base_url}/api/v1/collections/{self._collection_id}/query",
            {
                "query_embeddings": query_embeddings,
                "n_results": n_results,
                "where": where,
                "include": ["documents", "metadatas", "distances"],
            },
        )

    def delete(self, where: dict[str, Any]) -> None:
        _post_json(
            f"{self._base_url}/api/v1/collections/{self._collection_id}/delete",
            {"where": where},
        )


def get_collection() -> ChromaCollection:
    base_url = os.getenv("CHROMA_URL", "http://localhost:8000").rstrip("/")
    collection = _post_json(
        f"{base_url}/api/v1/collections",
        {
            "name": COLLECTION_NAME,
            "metadata": {"hnsw:space": "cosine"},
            "get_or_create": True,
        },
    )
    return ChromaCollection(collection["id"], base_url)


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=15) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"Chroma request failed: {detail}") from exc

    return json.loads(body) if body else {}
