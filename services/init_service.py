from __future__ import annotations

from core.command_session import CommandSession
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder


class InitService:
    def __init__(self, runner: InteractiveRunner, builder: SessionBuilder) -> None:
        self.runner = runner
        self.builder = builder

    def initialize(self, force: bool = False):
        session = CommandSession(self.builder.build_init(force), self.runner)
        return session.execute()

