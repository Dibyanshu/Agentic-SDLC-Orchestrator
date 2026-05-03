import unittest
from unittest.mock import patch

from app.context.context_builder import build_context


class ContextBuilderTests(unittest.TestCase):
    def test_build_context_limits_rag_chunks_to_three(self) -> None:
        chunks = [
            {"chunk_id": f"chunk-{index}", "content": f"context {index}"}
            for index in range(5)
        ]

        with patch("app.context.context_builder.retrieve_rag_chunks", return_value=chunks):
            context = build_context("PRD", {"PRD": {}}, project_id="project-1")

        self.assertEqual("PRD", context["stage"])
        self.assertEqual(3, len(context["rag_chunks"]))
        self.assertEqual("chunk-0", context["rag_chunks"][0]["chunk_id"])

    def test_build_context_deduplicates_rag_chunks_before_limit(self) -> None:
        chunks = [
            {"chunk_id": "chunk-1", "content": "Repeated context"},
            {"chunk_id": "chunk-2", "content": " repeated context "},
            {"chunk_id": "chunk-3", "content": "Unique context"},
        ]

        with patch("app.context.context_builder.retrieve_rag_chunks", return_value=chunks):
            context = build_context("PRD", {"PRD": {}}, project_id="project-1")

        self.assertEqual(["chunk-1", "chunk-3"], [chunk["chunk_id"] for chunk in context["rag_chunks"]])

    def test_build_context_skips_rag_without_project_id(self) -> None:
        context = build_context("BA", {"PRD": {"Features": "A"}})

        self.assertEqual([], context["rag_chunks"])
        self.assertIn("max_context_chunks=3", context["constraints"])


if __name__ == "__main__":
    unittest.main()
