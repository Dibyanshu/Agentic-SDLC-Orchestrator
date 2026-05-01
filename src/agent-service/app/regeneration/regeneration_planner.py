from app.regeneration.dependency_resolver import resolve_dependencies


def plan_regeneration(section: str, mode: str) -> list[str]:
    owner_node = _owner_node(section)
    if mode == "single":
        return [owner_node]

    dependent_nodes = [_owner_node(item) for item in resolve_dependencies(section)]
    plan = [owner_node, *dependent_nodes]
    return list(dict.fromkeys(plan))


def _owner_node(section: str) -> str:
    artifact_type = section.split(".", 1)[0]
    if artifact_type == "PRD":
        return "pm_node"
    if artifact_type == "BA":
        return "ba_node"
    if artifact_type == "ARCH":
        return "architect_node"
    return "manager_node"

