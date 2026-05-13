from __future__ import annotations

from core.command_session import CommandSession
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder
from repositories.avp_repository import AvpRepository


class AvpService:
    def __init__(self, runner: InteractiveRunner, builder: SessionBuilder, repository: AvpRepository) -> None:
        self.runner = runner
        self.builder = builder
        self.repository = repository

    def list_all(self) -> dict[str, dict[str, list[str]]]:
        return self.repository.load()

    def add(self, entity_type: str, name: str, values_csv: str):
        return CommandSession(self.builder.build_avp_add(entity_type, name, values_csv), self.runner).execute()

    def modify(self, entity_type: str, name: str, values_csv: str):
        return CommandSession(self.builder.build_avp_modify(entity_type, name, values_csv), self.runner).execute()

    def delete(self, entity_type: str, name: str):
        return CommandSession(self.builder.build_avp_delete(entity_type, name), self.runner).execute()

