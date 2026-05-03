PROMPT_TEMPLATE_VERSION = "2026-05-03.v1"

PM_SYSTEM_PROMPT = (
    "You are a senior product manager. Return only valid JSON with exactly "
    "these string keys: Overview, Features, UserFlow."
)

BA_SYSTEM_PROMPT = (
    "You are a senior business analyst. Return only valid JSON with exactly "
    "these string keys: UserStories, AcceptanceCriteria."
)

ARCHITECT_SYSTEM_PROMPT = (
    "You are a senior solution architect. Return only valid JSON with exactly "
    "these string keys: APIs, DBSchema, HLD, LLD."
)


def build_pm_user_prompt(raw_input: str) -> str:
    return (
        "Generate concise PRD sections for this product request.\n\n"
        f"Product request:\n{raw_input.strip() or 'Define the requested product capability.'}"
    )


def build_ba_user_prompt(prd: dict[str, str]) -> str:
    return (
        "Generate BA sections from these approved PRD sections.\n\n"
        f"PRD JSON:\n{prd}"
    )


def build_architect_user_prompt(ba: dict[str, str], prd: dict[str, str]) -> str:
    return (
        "Generate architecture sections from these approved BA and PRD sections.\n\n"
        f"BA JSON:\n{ba}\n\nPRD JSON:\n{prd}"
    )


PROMPT_TEMPLATES = {
    "pm_agent": PM_SYSTEM_PROMPT,
    "ba_agent": BA_SYSTEM_PROMPT,
    "architect_agent": ARCHITECT_SYSTEM_PROMPT,
}
