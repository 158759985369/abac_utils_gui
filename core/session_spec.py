from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SessionStep:
    phase: str
    prompt_pattern: str
    prompt_label: str
    response: str
    sensitive: bool = False
    recorded_response: str | None = None
    timeout: int | None = None
    send_newline: bool = True

    @property
    def logged_response(self) -> str:
        if self.recorded_response is not None:
            return self.recorded_response
        if self.sensitive:
            return "********"
        return self.response


@dataclass(slots=True)
class SessionSpec:
    name: str
    command: list[str]
    steps: list[SessionStep] = field(default_factory=list)
    timeout: int = 15
    exit_timeout: int = 10
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def known_prompt_patterns(self) -> list[str]:
        seen: list[str] = []
        for step in self.steps:
            if step.prompt_pattern not in seen:
                seen.append(step.prompt_pattern)
        return seen

