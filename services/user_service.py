from __future__ import annotations

from core.command_session import CommandSession
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder
from repositories.avp_repository import AvpRepository
from repositories.user_repository import UserRepository


class UserService:
    def __init__(
        self,
        runner: InteractiveRunner,
        builder: SessionBuilder,
        user_repository: UserRepository,
        avp_repository: AvpRepository,
    ) -> None:
        self.runner = runner
        self.builder = builder
        self.user_repository = user_repository
        self.avp_repository = avp_repository

    def list_users(self) -> list[dict[str, object]]:
        return self.user_repository.list_users()

    def add(self, username: str, selections: dict[str, str], password: str):
        avps = self.avp_repository.load()["user"]
        return CommandSession(
            self.builder.build_user_add(username, avps, selections, password),
            self.runner,
        ).execute()

    def delete(self, username: str):
        return CommandSession(self.builder.build_user_delete(username), self.runner).execute()

