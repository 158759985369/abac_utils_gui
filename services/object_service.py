from __future__ import annotations

from core.command_session import CommandSession
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder
from repositories.avp_repository import AvpRepository
from repositories.object_repository import ObjectRepository


class ObjectService:
    def __init__(
        self,
        runner: InteractiveRunner,
        builder: SessionBuilder,
        object_repository: ObjectRepository,
        avp_repository: AvpRepository,
    ) -> None:
        self.runner = runner
        self.builder = builder
        self.object_repository = object_repository
        self.avp_repository = avp_repository

    def list_entries(self) -> list[str]:
        return self.object_repository.list_shared_entries()

    def list_attrs(self) -> dict[str, dict[str, str]]:
        return self.object_repository.list_all_attrs()

    def get_attrs(self, object_path: str) -> dict[str, str]:
        return self.object_repository.get_attrs(object_path)

    def add(self, object_path: str, attr_name: str, value: str):
        avps = self.avp_repository.load()["obj"]
        current = self.object_repository.get_attrs(object_path)
        return CommandSession(
            self.builder.build_object_add(object_path, avps, current, attr_name, value),
            self.runner,
        ).execute()

    def change(self, object_path: str, attr_name: str, value: str):
        avps = self.avp_repository.load()["obj"]
        current = self.object_repository.get_attrs(object_path)
        return CommandSession(
            self.builder.build_object_change(object_path, avps, current, attr_name, value),
            self.runner,
        ).execute()

    def delete(self, object_path: str, attr_name: str):
        current = self.object_repository.get_attrs(object_path)
        return CommandSession(
            self.builder.build_object_delete(object_path, current, attr_name),
            self.runner,
        ).execute()

