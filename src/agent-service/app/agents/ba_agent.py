from typing import Any

from app.agents.agent_llm_runner import run_json_agent
from app.context.context_builder import build_context
from app.llm.prompt_templates import BA_SYSTEM_PROMPT, build_ba_user_prompt

REQUIRED_BA_KEYS = {"UserStories", "AcceptanceCriteria"}


def generate_ba(
    prd: dict[str, str],
    project_id: str,
    artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, str]:
    context = build_context("BA", artifacts or {"PRD": prd}, project_id=project_id)
    return run_json_agent(
        project_id=project_id,
        node_name="ba_node",
        agent_name="BA",
        system_prompt=BA_SYSTEM_PROMPT,
        user_prompt=build_ba_user_prompt(prd),
        context=context,
        required_keys=REQUIRED_BA_KEYS,
    )
