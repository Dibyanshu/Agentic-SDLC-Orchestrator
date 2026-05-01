def generate_architecture(ba: dict[str, str]) -> dict[str, str]:
    user_stories = ba.get("UserStories", "approved user stories")

    return {
        "APIs": f"Expose project, workflow, section, HITL, and logs APIs to support: {user_stories}",
        "DBSchema": "Use projects, artifacts, sections, section_versions, checkpoints, refinement_logs, and llm_logs tables.",
        "HLD": "Use .NET API as control plane and Python LangGraph service as orchestration engine.",
        "LLD": "Implement node contracts, context builder, LLM client, persistence adapters, and regeneration planner as separate modules.",
    }

