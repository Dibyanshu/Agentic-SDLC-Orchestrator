class LlmClient:
    def complete(self, system_prompt: str, user_prompt: str, context: dict[str, object]) -> dict[str, object]:
        return {
            "text": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "model": "stub",
        }

