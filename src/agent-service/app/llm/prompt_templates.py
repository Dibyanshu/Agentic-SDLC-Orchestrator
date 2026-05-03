PROMPT_TEMPLATE_VERSION = "2026-05-03.v1"

PM_SYSTEM_PROMPT = (
    "You are a senior product manager. Return only valid JSON with exactly "
    "these string keys: Overview, Features, UserFlow."
)


def build_pm_user_prompt(raw_input: str) -> str:
    return (
        "Generate concise PRD sections for this product request.\n\n"
        f"Product request:\n{raw_input.strip() or 'Define the requested product capability.'}"
    )


PROMPT_TEMPLATES = {
    "pm_agent": PM_SYSTEM_PROMPT,
    "ba_agent": "Generate BA sections as structured JSON.",
    "architect_agent": "Generate architecture sections as structured JSON.",
}
