import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


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
    def __init__(self) -> None:
        self._provider = os.getenv("LLM_PROVIDER", "stub").strip().lower()
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self._api_key = os.getenv("OPENAI_API_KEY", "").strip()

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict[str, Any],
    ) -> LlmResult:
        if self._provider == "openai":
            return self._complete_openai(system_prompt, user_prompt, context)

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
    ) -> LlmResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")

        start = time.perf_counter()
        request_payload = {
            "model": self._model,
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
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed: {exc.code} {error_body}") from exc

        body = json.loads(raw_body)
        message = body["choices"][0]["message"]["content"]
        usage = body.get("usage", {})
        return LlmResult(
            text=message,
            input_tokens=int(usage.get("prompt_tokens", 0)),
            output_tokens=int(usage.get("completion_tokens", 0)),
            model=body.get("model", self._model),
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
