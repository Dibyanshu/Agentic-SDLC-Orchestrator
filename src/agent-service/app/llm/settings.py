import os
from dataclasses import dataclass

AGENT_KEYS = ("pm", "ba", "architect")
PROVIDERS = ("stub", "openai", "gemini", "claude")
DEFAULT_AGENT_BUDGETS = {
    "pm": 3_000,
    "ba": 3_000,
    "architect": 4_000,
}


@dataclass(frozen=True)
class AgentLlmSettings:
    provider: str
    model: str
    token_budget: int


def default_agent_settings(agent_name: str) -> AgentLlmSettings:
    provider = os.getenv("LLM_PROVIDER", "stub").strip().lower() or "stub"
    if provider not in PROVIDERS:
        provider = "stub"

    return AgentLlmSettings(
        provider=provider,
        model=default_model_for_provider(provider),
        token_budget=DEFAULT_AGENT_BUDGETS.get(agent_name, 3_000),
    )


def default_model_for_provider(provider: str) -> str:
    if provider == "openai":
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    if provider == "claude":
        return os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022").strip() or "claude-3-5-sonnet-20241022"
    return "stub"


def provider_key_configured(provider: str) -> bool:
    if provider == "stub":
        return True
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY", "").strip())
    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY", "").strip())
    if provider == "claude":
        return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    return False


def agent_key_for_node(node_name: str) -> str:
    if node_name == "ba_node":
        return "ba"
    if node_name == "architect_node":
        return "architect"
    return "pm"


def validate_agent_settings(settings: AgentLlmSettings) -> None:
    if settings.provider not in PROVIDERS:
        raise ValueError(f"provider must be one of: {', '.join(PROVIDERS)}")
    if not settings.model.strip():
        raise ValueError("model is required")
    if settings.provider in {"gemini", "openai", "claude"} and any(
        character.isspace() for character in settings.model
    ):
        raise ValueError("model must be an API model id without spaces")
    if settings.token_budget < 100 or settings.token_budget > 200_000:
        raise ValueError("tokenBudget must be between 100 and 200000")
