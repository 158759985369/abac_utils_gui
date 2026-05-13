from __future__ import annotations

from dataclasses import dataclass

from core.command_result import CommandResult
from core.interactive_runner import InteractiveRunner
from core.session_spec import SessionSpec


@dataclass(slots=True)
class CommandSession:
    spec: SessionSpec
    runner: InteractiveRunner

    def execute(self) -> CommandResult:
        return self.runner.run(self.spec)

