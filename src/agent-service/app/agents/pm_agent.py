import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.context.context_builder import build_context
from app.llm.llm_client import LlmClient
from app.llm.prompt_templates import (
    PM_SYSTEM_PROMPT,
    PROMPT_TEMPLATE_VERSION,
    build_pm_user_prompt,
)
from app.logging.llm_logger import LlmLogger

REQUIRED_PRD_KEYS = {"Overview", "Features", "UserFlow"}


def generate_prd(
    raw_input: str,
    project_id: str,
    artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, str]:
    context = build_context("PRD", artifacts or {})
    system_prompt = PM_SYSTEM_PROMPT
    user_prompt = build_pm_user_prompt(raw_input)
    cache_key = _cache_key(system_prompt, user_prompt, context)
    logger = LlmLogger()
    client = LlmClient()

    last_error: Exception | None = None
    for attempt in range(1, 4):
        start_time = datetime.now(timezone.utc)
        try:
            result = client.complete(system_prompt, user_prompt, context)
            payload = _parse_prd_json(result.text)
            end_time = datetime.now(timezone.utc)
            logger.log(
                {
                    "project_id": project_id,
                    "node_name": "pm_node",
                    "agent_name": "PM",
                    "model_name": result.model,
                    "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "context_payload": context,
                    "response_text": result.text,
                    "response_format": "json",
                    "status": "success",
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "total_tokens": result.input_tokens + result.output_tokens,
                    "estimated_cost": 0,
                    "latency_ms": result.latency_ms,
                    "cache_hit": result.cache_hit,
                    "cache_key": cache_key,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )
            return payload
        except Exception as exc:
            last_error = exc
            end_time = datetime.now(timezone.utc)
            logger.log(
                {
                    "project_id": project_id,
                    "node_name": "pm_node",
                    "agent_name": "PM",
                    "model_name": "unknown",
                    "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "context_payload": {**context, "attempt": attempt},
                    "response_text": None,
                    "response_format": "json",
                    "status": "failure",
                    "error_message": str(exc),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost": 0,
                    "latency_ms": int((end_time - start_time).total_seconds() * 1000),
                    "cache_hit": False,
                    "cache_key": cache_key,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )

    raise RuntimeError(f"PM agent failed after 3 attempts: {last_error}")


def _parse_prd_json(text: str) -> dict[str, str]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("PM response must be a JSON object.")

    missing = REQUIRED_PRD_KEYS.difference(payload.keys())
    if missing:
        raise ValueError(f"PM response is missing keys: {', '.join(sorted(missing))}")

    return {key: str(payload[key]) for key in sorted(REQUIRED_PRD_KEYS)}


def _cache_key(
    system_prompt: str,
    user_prompt: str,
    context: dict[str, Any],
) -> str:
    raw = json.dumps(
        {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "context": context,
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
