def generate_prd(raw_input: str) -> dict[str, str]:
    goal = raw_input.strip() or "Define the requested product capability."

    return {
        "Overview": f"Build an Agentic SDLC workflow for: {goal}",
        "Features": "Project initialization, deterministic workflow execution, HITL checkpoints, section management, and audit logging.",
        "UserFlow": "User creates a project, starts workflow generation, reviews PRD output, and approves or refines sections.",
    }

