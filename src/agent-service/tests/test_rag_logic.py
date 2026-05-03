import unittest

from app.context.embeddings import VECTOR_DIMENSION, embed_text
from app.context.text_chunker import chunk_text
from app.regeneration.regeneration_planner import plan_regeneration


class RagLogicTests(unittest.TestCase):
    def test_embed_text_is_deterministic_and_normalized(self) -> None:
        first = embed_text("Controlled RAG context")
        second = embed_text("Controlled RAG context")

        self.assertEqual(first, second)
        self.assertEqual(VECTOR_DIMENSION, len(first))
        self.assertAlmostEqual(1.0, sum(value * value for value in first), places=6)

    def test_chunk_text_splits_large_sources_with_overlap(self) -> None:
        text = "A" * 1_300 + "B" * 1_300
        chunks = chunk_text(text)

        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(max(len(chunk) for chunk in chunks), 1_200)
        self.assertTrue(chunks[1].startswith("A"))

    def test_cascade_regeneration_deduplicates_node_plan(self) -> None:
        plan = plan_regeneration("PRD.Features", "cascade")

        self.assertEqual(["pm_node", "ba_node", "architect_node"], plan)

    def test_single_regeneration_only_runs_owner(self) -> None:
        plan = plan_regeneration("BA.UserStories", "single")

        self.assertEqual(["ba_node"], plan)


if __name__ == "__main__":
    unittest.main()
