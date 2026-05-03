import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.llm.settings import AgentLlmSettings


@dataclass(frozen=True)
class LlmResult:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: int
    cache_hit: bool = False
    cache_key: str | None = None


class LlmClient:
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        settings: AgentLlmSettings,
        required_keys: set[str],
    ) -> LlmResult:
        if settings.provider == "openai":
            return self._complete_openai(system_prompt, user_prompt, context, settings)
        if settings.provider == "gemini":
            return self._complete_gemini(system_prompt, user_prompt, context, settings, required_keys)
        if settings.provider == "claude":
            return self._complete_claude(system_prompt, user_prompt, context, settings)

        return self._complete_stub(user_prompt, system_prompt, context)

    def _complete_stub(
        self,
        user_prompt: str,
        system_prompt: str,
        context: dict[str, Any],
    ) -> LlmResult:
        start = time.perf_counter()
        payload = _stub_payload(system_prompt, user_prompt)
        text = json.dumps(payload)
        return LlmResult(
            text=text,
            input_tokens=_estimate_tokens(
                f"{system_prompt}\n{user_prompt}\n{json.dumps(context, sort_keys=True)}"
            ),
            output_tokens=_estimate_tokens(text),
            model="stub",
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    def _complete_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        settings: AgentLlmSettings,
    ) -> LlmResult:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise LlmConfigurationError("OPENAI_API_KEY is required for OpenAI provider.")

        start = time.perf_counter()
        request_payload = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{user_prompt}\n\nContext JSON:\n"
                        f"{json.dumps(context, sort_keys=True)}"
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {400, 401, 403, 404, 429}:
                raise LlmConfigurationError(f"OpenAI request failed: {exc.code} {error_body}") from exc
            raise RuntimeError(f"OpenAI request failed: {exc.code} {error_body}") from exc

        body = json.loads(raw_body)
        message = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return LlmResult(
            text=message,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            model=f"openai:{body.get('model', settings.model)}",
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    def _complete_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        settings: AgentLlmSettings,
        required_keys: set[str],
    ) -> LlmResult:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise LlmConfigurationError("GEMINI_API_KEY is required for Gemini provider.")

        start = time.perf_counter()
        request_payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                f"{system_prompt}\n\n{user_prompt}\n\nContext JSON:\n"
                                f"{json.dumps(context, sort_keys=True)}"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": _json_object_schema(required_keys),
                "maxOutputTokens": 2048,
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.model}:generateContent"
        request = urllib.request.Request(
            url,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {400, 401, 403, 404, 429}:
                raise LlmConfigurationError(f"Gemini request failed: {exc.code} {error_body}") from exc
            raise RuntimeError(f"Gemini request failed: {exc.code} {error_body}") from exc

        body = json.loads(raw_body)
        parts = body["candidates"][0]["content"].get("parts", [])
        message = "".join(part.get("text", "") for part in parts)
        usage = body.get("usageMetadata", {})
        return LlmResult(
            text=message,
            input_tokens=int(usage.get("promptTokenCount", 0)),
            output_tokens=int(usage.get("candidatesTokenCount", 0)),
            model=f"gemini:{settings.model}",
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    def _complete_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
        settings: AgentLlmSettings,
    ) -> LlmResult:
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise LlmConfigurationError("ANTHROPIC_API_KEY is required for Claude provider.")

        start = time.perf_counter()
        request_payload = {
            "model": settings.model,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{user_prompt}\n\nContext JSON:\n"
                        f"{json.dumps(context, sort_keys=True)}\n\nReturn only valid JSON."
                    ),
                }
            ],
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {400, 401, 403, 404}:
                raise LlmConfigurationError(f"Claude request failed: {exc.code} {error_body}") from exc
            raise RuntimeError(f"Claude request failed: {exc.code} {error_body}") from exc

        body = json.loads(raw_body)
        message = "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        usage = body.get("usage", {})
        return LlmResult(
            text=message,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            model=f"claude:{body.get('model', settings.model)}",
            latency_ms=int((time.perf_counter() - start) * 1000),
        )


def _extract_product_request(user_prompt: str) -> str:
    marker = "Product request:"
    if marker not in user_prompt:
        return user_prompt.strip() or "Define the requested product capability."

    return user_prompt.split(marker, 1)[1].strip()


def _stub_payload(system_prompt: str, user_prompt: str) -> dict[str, str]:
    if "UserStories" in system_prompt:
        return {
            "UserStories": (
                "As a product owner, I want approved PRD features converted into "
                "clear implementation-ready stories so that delivery teams can plan work."
            ),
            "AcceptanceCriteria": (
                "Given approved PRD sections, when BA generation runs, then user stories "
                "and acceptance criteria are produced and paused for human approval."
            ),
        }

    if "DBSchema" in system_prompt:
        return {
            "APIs": (
                "Expose project, workflow, section, HITL, logs, and checkpoint APIs "
                "for the orchestrator control plane."
            ),
            "DBSchema": (
                "Use projects, artifacts, sections, section_versions, checkpoints, "
                "refinement_logs, llm_logs, and llm_context_chunks tables."
            ),
            "HLD": (
                "Use .NET API as the control plane and Python FastAPI agent service "
                "as the orchestration engine."
            ),
            "LLD": (
                "Keep nodes, agents, context building, LLM execution, persistence, "
                "and regeneration planning in separate modules."
            ),
        }

    goal = _extract_product_request(user_prompt)
    return {
        "Overview": f"Build an Agentic SDLC workflow for: {goal}",
        "Features": (
            "Project initialization, deterministic workflow execution, "
            "HITL checkpoints, section management, and audit logging."
        ),
        "UserFlow": (
            "User creates a project, starts workflow generation, reviews PRD "
            "output, and approves or refines sections."
        ),
    }


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _json_object_schema(required_keys: set[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {key: {"type": "string"} for key in sorted(required_keys)},
        "required": sorted(required_keys),
        "additionalProperties": False,
    }


class LlmConfigurationError(RuntimeError):
    pass
