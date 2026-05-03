import os
from collections.abc import Mapping, Sequence
from typing import Any

import pymysql
from pymysql.connections import Connection


class MysqlClient:
    def __init__(self, connection_string: str | None = None) -> None:
        self._settings = _parse_connection_string(
            connection_string or os.getenv("DB_CONNECTION", "")
        )

    def connect(self) -> Connection:
        return pymysql.connect(
            host=self._settings.get("server", "localhost"),
            port=int(self._settings.get("port", "3306")),
            database=self._settings.get("database", "agentic_sdlc"),
            user=self._settings.get("user", "agentic"),
            password=self._settings.get("password", "agentic_password"),
            autocommit=False,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

    def ping(self) -> bool:
        with self.connect() as connection:
            connection.ping(reconnect=True)
        return True


def _parse_connection_string(connection_string: str) -> Mapping[str, str]:
    settings: dict[str, str] = {}
    for part in connection_string.split(";"):
        if not part.strip() or "=" not in part:
            continue

        key, value = part.split("=", 1)
        settings[key.strip().lower()] = value.strip()

    return settings


SqlParams = Mapping[str, Any] | Sequence[Any] | None
