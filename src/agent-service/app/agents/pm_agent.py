from typing import Any

from app.agents.agent_llm_runner import run_json_agent
from app.context.context_builder import build_context
from app.llm.prompt_templates import (
    PM_SYSTEM_PROMPT,
    build_pm_user_prompt,
)

REQUIRED_PRD_KEYS = {"Overview", "Features", "UserFlow"}


def generate_prd(
    raw_input: str,
    project_id: str,
    artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, str]:
    context = build_context("PRD", artifacts or {}, project_id=project_id)
    return run_json_agent(
        project_id=project_id,
        node_name="pm_node",
        agent_name="PM",
        system_prompt=PM_SYSTEM_PROMPT,
        user_prompt=build_pm_user_prompt(raw_input),
        context=context,
        required_keys=REQUIRED_PRD_KEYS,
    )
