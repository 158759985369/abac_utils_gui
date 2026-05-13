from __future__ import annotations

import json
import pwd
from pathlib import Path


class UserRepository:
    def __init__(self, path: str = "/etc/abac/user_attr.json") -> None:
        self.path = Path(path)

    def list_users(self) -> list[dict[str, object]]:
        if not self.path.is_file():
            return []
        with self.path.open(encoding="utf-8") as handle:
            raw_users = json.load(handle).get("users", {})

        rows: list[dict[str, object]] = []
        for username, payload in raw_users.items():
            exists_in_system = True
            try:
                pwd.getpwnam(username)
            except KeyError:
                exists_in_system = False
            rows.append(
                {
                    "username": username,
                    "uid": payload.get("uid"),
                    "avps": payload.get("avps", {}),
                    "exists_in_system": exists_in_system,
                }
            )
        rows.sort(key=lambda item: str(item["username"]))
        return rows

