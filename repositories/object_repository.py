from __future__ import annotations

import json
from pathlib import Path


class ObjectRepository:
    def __init__(
        self,
        attrs_path: str = "/etc/abac/obj_attr.json",
        shared_dir: str = "/home/secured/",
    ) -> None:
        self.attrs_path = Path(attrs_path)
        self.shared_dir = Path(shared_dir)

    def list_all_attrs(self) -> dict[str, dict[str, str]]:
        if not self.attrs_path.is_file():
            return {}
        with self.attrs_path.open(encoding="utf-8") as handle:
            return json.load(handle).get("objects", {})

    def get_attrs(self, object_path: str) -> dict[str, str]:
        return self.list_all_attrs().get(str(Path(object_path)), {})

    def list_shared_entries(self) -> list[str]:
        if not self.shared_dir.exists():
            return []
        paths = [str(path) for path in self.shared_dir.rglob("*")]
        return sorted(paths)

