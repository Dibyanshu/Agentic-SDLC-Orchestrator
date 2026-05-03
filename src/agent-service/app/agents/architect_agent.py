from typing import Any

from app.agents.agent_llm_runner import run_json_agent
from app.context.context_builder import build_context
from app.llm.prompt_templates import (
    ARCHITECT_SYSTEM_PROMPT,
    build_architect_user_prompt,
)

REQUIRED_ARCH_KEYS = {"APIs", "DBSchema", "HLD", "LLD"}


def generate_architecture(
    ba: dict[str, str],
    project_id: str,
    artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, str]:
    current_artifacts = artifacts or {"BA": ba}
    context = build_context("ARCH", current_artifacts, project_id=project_id)
    return run_json_agent(
        project_id=project_id,
        node_name="architect_node",
        agent_name="Architect",
        system_prompt=ARCHITECT_SYSTEM_PROMPT,
        user_prompt=build_architect_user_prompt(
            ba,
            current_artifacts.get("PRD", {}),
        ),
        context=context,
        required_keys=REQUIRED_ARCH_KEYS,
    )
