import unittest

from app.llm.token_budget import (
    TokenBudgetExceededError,
    estimate_input_tokens,
    token_budget_for_node,
    validate_token_budget,
)


class TokenBudgetTests(unittest.TestCase):
    def test_known_node_budgets(self) -> None:
        self.assertEqual(3_000, token_budget_for_node("pm_node"))
        self.assertEqual(3_000, token_budget_for_node("ba_node"))
        self.assertEqual(4_000, token_budget_for_node("architect_node"))

    def test_estimate_input_tokens_includes_context(self) -> None:
        tokens = estimate_input_tokens(
            "system words",
            "user words",
            {"rag_chunks": [{"content": "context words"}]},
        )

        self.assertGreaterEqual(tokens, 6)

    def test_validate_token_budget_raises_before_llm_call(self) -> None:
        oversized_prompt = "token " * 3_100

        with self.assertRaises(TokenBudgetExceededError) as raised:
            validate_token_budget(
                node_name="pm_node",
                system_prompt="system",
                user_prompt=oversized_prompt,
                context={},
            )

        self.assertEqual("pm_node", raised.exception.node_name)
        self.assertGreater(raised.exception.estimated_tokens, raised.exception.budget)


if __name__ == "__main__":
    unittest.main()
