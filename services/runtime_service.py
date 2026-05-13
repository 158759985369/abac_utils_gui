from __future__ import annotations

from core.command_session import CommandSession
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder
from repositories.status_probe import StatusProbe


class RuntimeService:
    def __init__(self, runner: InteractiveRunner, builder: SessionBuilder, probe: StatusProbe) -> None:
        self.runner = runner
        self.builder = builder
        self.probe = probe

    def load(self):
        return CommandSession(self.builder.build_load(), self.runner).execute()

    def snapshot(self) -> dict[str, object]:
        return self.probe.snapshot()

