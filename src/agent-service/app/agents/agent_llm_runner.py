import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.llm.llm_client import LlmClient
from app.llm.prompt_templates import PROMPT_TEMPLATE_VERSION
from app.logging.llm_logger import LlmLogger


def run_json_agent(
    *,
    project_id: str,
    node_name: str,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    context: dict[str, Any],
    required_keys: set[str],
) -> dict[str, str]:
    cache_key = _cache_key(system_prompt, user_prompt, context)
    logger = LlmLogger()
    client = LlmClient()

    last_error: Exception | None = None
    for attempt in range(1, 4):
        start_time = datetime.now(timezone.utc)
        try:
            result = client.complete(system_prompt, user_prompt, context)
            payload = _parse_required_json(result.text, required_keys, agent_name)
            end_time = datetime.now(timezone.utc)
            logger.log(
                {
                    "project_id": project_id,
                    "node_name": node_name,
                    "agent_name": agent_name,
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
                    "node_name": node_name,
                    "agent_name": agent_name,
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

    raise RuntimeError(f"{agent_name} agent failed after 3 attempts: {last_error}")


def _parse_required_json(
    text: str,
    required_keys: set[str],
    agent_name: str,
) -> dict[str, str]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError(f"{agent_name} response must be a JSON object.")

    missing = required_keys.difference(payload.keys())
    if missing:
        raise ValueError(
            f"{agent_name} response is missing keys: {', '.join(sorted(missing))}"
        )

    return {key: str(payload[key]) for key in sorted(required_keys)}


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
