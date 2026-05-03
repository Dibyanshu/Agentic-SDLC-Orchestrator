from typing import Any

from app.llm.settings import (
    AGENT_KEYS,
    PROVIDERS,
    AgentLlmSettings,
    default_agent_settings,
    default_model_for_provider,
    provider_key_configured,
    validate_agent_settings,
)
from app.persistence.mysql_client import MysqlClient


class LlmSettingsStore:
    def __init__(self, mysql_client: MysqlClient | None = None) -> None:
        self._mysql = mysql_client or MysqlClient()

    def list_providers(self) -> list[dict[str, Any]]:
        return [
            {
                "provider": provider,
                "default_model": default_model_for_provider(provider),
                "api_key_configured": provider_key_configured(provider),
            }
            for provider in PROVIDERS
        ]

    def get_project_settings(self, project_id: str) -> dict[str, AgentLlmSettings]:
        self._ensure_table()
        with self._mysql.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT agent_name, provider, model, token_budget
                    FROM project_llm_settings
                    WHERE project_id = %s
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        settings = {agent: default_agent_settings(agent) for agent in AGENT_KEYS}
        for row in rows:
            agent = row["agent_name"]
            if agent in settings:
                settings[agent] = AgentLlmSettings(
                    provider=row["provider"],
                    model=row["model"],
                    token_budget=int(row["token_budget"]),
                )

        return settings

    def get_agent_settings(self, project_id: str, agent_name: str) -> AgentLlmSettings:
        return self.get_project_settings(project_id).get(
            agent_name,
            default_agent_settings(agent_name),
        )

    def save_project_settings(
        self,
        project_id: str,
        settings: dict[str, AgentLlmSettings],
    ) -> dict[str, AgentLlmSettings]:
        self._ensure_table()
        normalized = _normalize_settings(settings)

        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    for agent_name, agent_settings in normalized.items():
                        cursor.execute(
                            """
                            INSERT INTO project_llm_settings (
                              project_id, agent_name, provider, model, token_budget
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                              provider = VALUES(provider),
                              model = VALUES(model),
                              token_budget = VALUES(token_budget),
                              updated_at = CURRENT_TIMESTAMP
                            """,
                            (
                                project_id,
                                agent_name,
                                agent_settings.provider,
                                agent_settings.model,
                                agent_settings.token_budget,
                            ),
                        )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return self.get_project_settings(project_id)

    def _ensure_table(self) -> None:
        with self._mysql.connect() as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS project_llm_settings (
                          project_id VARCHAR(50) NOT NULL,
                          agent_name VARCHAR(50) NOT NULL,
                          provider VARCHAR(50) NOT NULL,
                          model VARCHAR(100) NOT NULL,
                          token_budget INT NOT NULL,
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                          PRIMARY KEY (project_id, agent_name),
                          CONSTRAINT fk_project_llm_settings_projects FOREIGN KEY (project_id) REFERENCES projects(id)
                        )
                        """
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise


def _normalize_settings(settings: dict[str, AgentLlmSettings]) -> dict[str, AgentLlmSettings]:
    normalized: dict[str, AgentLlmSettings] = {}
    for agent_name in AGENT_KEYS:
        agent_settings = settings.get(agent_name, default_agent_settings(agent_name))
        normalized_settings = AgentLlmSettings(
            provider=agent_settings.provider.strip().lower(),
            model=agent_settings.model.strip(),
            token_budget=int(agent_settings.token_budget),
        )
        validate_agent_settings(normalized_settings)
        normalized[agent_name] = normalized_settings

    return normalized
