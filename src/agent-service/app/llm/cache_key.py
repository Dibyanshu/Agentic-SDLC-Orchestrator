import hashlib
import json
from typing import Any

from app.llm.settings import AgentLlmSettings


def build_cache_key(
    system_prompt: str,
    user_prompt: str,
    context: dict[str, Any],
    settings: AgentLlmSettings,
) -> str:
    raw = json.dumps(
        {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "context": context,
            "provider": settings.provider,
            "model": settings.model,
            "token_budget": settings.token_budget,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
