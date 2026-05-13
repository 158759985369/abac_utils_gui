from __future__ import annotations

import json
from pathlib import Path


class AvpRepository:
    def __init__(self, path: str = "/etc/abac/avp.json") -> None:
        self.path = Path(path)

    def load(self) -> dict[str, dict[str, list[str]]]:
        if not self.path.is_file():
            return {"user": {}, "obj": {}, "env": {}}
        with self.path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return {
            "user": data.get("user", {}),
            "obj": data.get("obj", {}),
            "env": data.get("env", {}),
        }

