from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class PromptHit:
    phase: str
    prompt_label: str
    prompt_text: str
    timestamp: datetime


@dataclass(slots=True)
class SentInput:
    phase: str
    value: str
    sensitive: bool
    timestamp: datetime


@dataclass(slots=True)
class CommandResult:
    session_name: str
    command: list[str]
    started_at: datetime
    finished_at: datetime | None = None
    stdout: str = ""
    stderr: str = ""
    combined_output: str = ""
    prompt_hits: list[PromptHit] = field(default_factory=list)
    sent_inputs: list[SentInput] = field(default_factory=list)
    exit_code: int | None = None
    final_phase: str = "NOT_STARTED"
    error_message: str | None = None
    log_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.error_message is None and self.exit_code == 0

    @property
    def duration_seconds(self) -> float:
        if not self.finished_at:
            return 0.0
        return max(0.0, (self.finished_at - self.started_at).total_seconds())

    @property
    def command_text(self) -> str:
        return " ".join(self.command)

    def short_summary(self) -> str:
        if self.success:
            return f"{self.session_name} succeeded"
        if self.error_message:
            return f"{self.session_name} failed: {self.error_message}"
        return f"{self.session_name} failed with exit code {self.exit_code}"

    def as_log_text(self) -> str:
        prompt_lines = "\n".join(
            f"- [{hit.timestamp.isoformat()}] {hit.phase} -> {hit.prompt_label}: {hit.prompt_text}"
            for hit in self.prompt_hits
        ) or "- <none>"
        input_lines = "\n".join(
            f"- [{sent.timestamp.isoformat()}] {sent.phase} -> {sent.value}"
            for sent in self.sent_inputs
        ) or "- <none>"

        return "\n".join(
            [
                f"session: {self.session_name}",
                f"command: {self.command_text}",
                f"started_at: {self.started_at.isoformat()}",
                f"finished_at: {self.finished_at.isoformat() if self.finished_at else ''}",
                f"duration_seconds: {self.duration_seconds:.3f}",
                f"exit_code: {self.exit_code}",
                f"final_phase: {self.final_phase}",
                f"error_message: {self.error_message or ''}",
                "",
                "prompt_hits:",
                prompt_lines,
                "",
                "sent_inputs:",
                input_lines,
                "",
                "stdout:",
                self.stdout,
                "",
                "stderr:",
                self.stderr,
                "",
                "combined_output:",
                self.combined_output,
            ]
        )

