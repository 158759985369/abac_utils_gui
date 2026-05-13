from __future__ import annotations

import json
from pathlib import Path


class PolicyRepository:
    def __init__(self, path: str = "/etc/abac/policy.json") -> None:
        self.path = Path(path)

    def list_rules(self) -> list[dict[str, object]]:
        if not self.path.is_file():
            return []
        with self.path.open(encoding="utf-8") as handle:
            return json.load(handle).get("rules", [])

    @staticmethod
    def render_rule(rule: dict[str, object]) -> str:
        user_part = " ^ ".join(f"{name}={value}" for name, value in dict(rule.get("user", {})).items())
        obj_part = " ^ ".join(f"{name}={value}" for name, value in dict(rule.get("obj", {})).items())
        env_map = dict(rule.get("env", {}))
        env_part = " ^ ".join(f"{name}={value}" for name, value in env_map.items()) if env_map else "*"
        return f"{user_part} | {obj_part} | {env_part} |{rule.get('op', '')}"

