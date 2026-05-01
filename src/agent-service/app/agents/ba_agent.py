def generate_ba(prd: dict[str, str]) -> dict[str, str]:
    features = prd.get("Features", "the approved product features")

    return {
        "UserStories": f"As a product owner, I want {features} so that early SDLC artifacts are generated consistently.",
        "AcceptanceCriteria": "Given a project input, when the workflow runs, then PRD sections are generated and paused for human approval.",
    }

