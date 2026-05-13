from __future__ import annotations

from core.command_result import CommandResult


def command_result_to_text(result: CommandResult) -> str:
    headline = result.short_summary()
    log_line = f"Log file: {result.log_path}" if result.log_path else "Log file: <not written>"
    return "\n".join([headline, f"Command: {result.command_text}", log_line, "", result.as_log_text()])


def dict_to_pretty_lines(data: dict[str, object]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)

