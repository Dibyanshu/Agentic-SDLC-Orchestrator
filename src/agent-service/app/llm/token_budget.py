import json
from typing import Any

NODE_TOKEN_BUDGETS = {
    "pm_node": 3_000,
    "ba_node": 3_000,
    "architect_node": 4_000,
}


def estimate_input_tokens(system_prompt: str, user_prompt: str, context: dict[str, Any]) -> int:
    context_text = json.dumps(context, sort_keys=True)
    return _estimate_tokens(f"{system_prompt}\n{user_prompt}\n{context_text}")


def token_budget_for_node(node_name: str) -> int:
    return NODE_TOKEN_BUDGETS.get(node_name, 3_000)


def validate_token_budget(
    *,
    node_name: str,
    system_prompt: str,
    user_prompt: str,
    context: dict[str, Any],
) -> int:
    estimated_tokens = estimate_input_tokens(system_prompt, user_prompt, context)
    budget = token_budget_for_node(node_name)
    if estimated_tokens > budget:
        raise TokenBudgetExceededError(node_name, estimated_tokens, budget)

    return estimated_tokens


class TokenBudgetExceededError(ValueError):
    def __init__(self, node_name: str, estimated_tokens: int, budget: int) -> None:
        super().__init__(
            f"{node_name} input token estimate {estimated_tokens} exceeds budget {budget}"
        )
        self.node_name = node_name
        self.estimated_tokens = estimated_tokens
        self.budget = budget


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))
