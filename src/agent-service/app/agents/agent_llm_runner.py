import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.llm.llm_client import LlmClient
from app.llm.prompt_templates import PROMPT_TEMPLATE_VERSION
from app.llm.token_budget import TokenBudgetExceededError, validate_token_budget
from app.logging.llm_logger import LlmLogger
from app.persistence.llm_cache_store import LlmCacheStore


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
    cache = LlmCacheStore()
    client = LlmClient()
    start_time = datetime.now(timezone.utc)

    try:
        estimated_input_tokens = validate_token_budget(
            node_name=node_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
        )
    except TokenBudgetExceededError as exc:
        end_time = datetime.now(timezone.utc)
        logger.log(
            {
                "project_id": project_id,
                "node_name": node_name,
                "agent_name": agent_name,
                "model_name": "budget_guard",
                "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "context_payload": {
                    **context,
                    "token_budget": exc.budget,
                    "estimated_input_tokens": exc.estimated_tokens,
                },
                "response_text": None,
                "response_format": "json",
                "status": "token_budget_exceeded",
                "error_message": str(exc),
                "input_tokens": exc.estimated_tokens,
                "output_tokens": 0,
                "total_tokens": exc.estimated_tokens,
                "estimated_cost": 0,
                "latency_ms": int((end_time - start_time).total_seconds() * 1000),
                "cache_hit": False,
                "cache_key": cache_key,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        raise

    cached = cache.get(cache_key)
    if cached is not None:
        payload = _parse_required_json(cached["response_text"], required_keys, agent_name)
        end_time = datetime.now(timezone.utc)
        logger.log(
            {
                "project_id": project_id,
                "node_name": node_name,
                "agent_name": agent_name,
                "model_name": cached["model_name"],
                "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "context_payload": context,
                "response_text": cached["response_text"],
                "response_format": "json",
                "status": "success",
                "input_tokens": cached["input_tokens"],
                "output_tokens": cached["output_tokens"],
                "total_tokens": cached["input_tokens"] + cached["output_tokens"],
                "estimated_cost": 0,
                "latency_ms": int((end_time - start_time).total_seconds() * 1000),
                "cache_hit": True,
                "cache_key": cache_key,
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        return payload

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
            cache.set(
                cache_key=cache_key,
                model_name=result.model,
                response_text=result.text,
                input_tokens=result.input_tokens or estimated_input_tokens,
                output_tokens=result.output_tokens,
                context_payload=context,
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
