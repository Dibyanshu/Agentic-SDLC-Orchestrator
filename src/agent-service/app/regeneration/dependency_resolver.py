DEPENDENCY_MAP = {
    "PRD.Features": ["BA.UserStories", "ARCH.APIs", "ARCH.DBSchema"],
    "BA.UserStories": ["ARCH.APIs", "ARCH.DBSchema"],
    "ARCH.APIs": ["ARCH.DBSchema"],
}


def resolve_dependencies(section: str) -> list[str]:
    return DEPENDENCY_MAP.get(section, [])

