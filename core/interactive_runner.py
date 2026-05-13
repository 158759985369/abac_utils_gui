from __future__ import annotations

import os
import platform
import shlex
import tempfile
from datetime import datetime
from pathlib import Path

from core.command_result import CommandResult, PromptHit, SentInput
from core.session_spec import SessionSpec


class InteractiveRunner:
    def __init__(self, log_dir: str = "/var/log/abac_gui", state_dir: str = "/var/lib/abac_gui") -> None:
        self.log_dir = Path(log_dir)
        self.state_dir = Path(state_dir)

    def run(self, spec: SessionSpec) -> CommandResult:
        started_at = datetime.now()
        result = CommandResult(
            session_name=spec.name,
            command=spec.command,
            started_at=started_at,
            metadata=dict(spec.metadata),
        )

        if platform.system() != "Linux":
            result.error_message = "ABAC GUI only supports Linux runtime."
            result.finished_at = datetime.now()
            result.final_phase = "UNSUPPORTED_PLATFORM"
            return result

        tmp_dir = None
        child = None
        stdout_path: Path | None = None
        stderr_path: Path | None = None

        try:
            import pexpect  # type: ignore

            tmp_dir = self._create_session_dir()
            stdout_path = tmp_dir / "stdout.log"
            stderr_path = tmp_dir / "stderr.log"
            stdout_path.touch()
            stderr_path.touch()

            command_text = shlex.join(spec.command)
            wrapped_command = (
                f"set -o pipefail; {command_text} "
                f"> >(tee -a {shlex.quote(str(stdout_path))}) "
                f"2> >(tee -a {shlex.quote(str(stderr_path))} >&2)"
            )
            environment = os.environ.copy()
            environment.update(spec.env)
            child = pexpect.spawn(
                "/bin/bash",
                ["-lc", wrapped_command],
                encoding="utf-8",
                timeout=spec.timeout,
                cwd=spec.cwd,
                env=environment,
            )

            transcript: list[str] = []
            result.final_phase = "STARTED"
            known_patterns = spec.known_prompt_patterns

            for step in spec.steps:
                result.final_phase = step.phase
                current_pattern = step.prompt_pattern
                unexpected_patterns = [pattern for pattern in known_patterns if pattern != current_pattern]
                pattern_list = [current_pattern, *unexpected_patterns, pexpect.EOF, pexpect.TIMEOUT]
                match_index = child.expect(pattern_list, timeout=step.timeout or spec.timeout)
                transcript.append(child.before or "")

                if match_index == 0:
                    prompt_text = child.after or ""
                    transcript.append(prompt_text)
                    now = datetime.now()
                    result.prompt_hits.append(
                        PromptHit(
                            phase=step.phase,
                            prompt_label=step.prompt_label,
                            prompt_text=prompt_text,
                            timestamp=now,
                        )
                    )
                    if step.send_newline:
                        child.sendline(step.response)
                    else:
                        child.send(step.response)
                    result.sent_inputs.append(
                        SentInput(
                            phase=step.phase,
                            value=step.logged_response,
                            sensitive=step.sensitive,
                            timestamp=now,
                        )
                    )
                elif 1 <= match_index <= len(unexpected_patterns):
                    unexpected = child.after or ""
                    transcript.append(unexpected)
                    raise RuntimeError(
                        f"Unexpected prompt while in phase {step.phase}: {unexpected.strip()}"
                    )
                elif match_index == len(unexpected_patterns) + 1:
                    raise RuntimeError(f"Command exited before expected prompt in phase {step.phase}")
                else:
                    raise TimeoutError(f"Timed out waiting for prompt in phase {step.phase}")

            while True:
                match_index = child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=spec.exit_timeout)
                transcript.append(child.before or "")
                if match_index == 0:
                    break
                raise TimeoutError(f"Timed out waiting for command completion in phase {result.final_phase}")

            child.close()
            result.exit_code = child.exitstatus if child.exitstatus is not None else child.status
            result.final_phase = "COMPLETED"
            result.combined_output = "".join(transcript)
        except Exception as exc:  # noqa: BLE001
            if child is not None:
                try:
                    child.close(force=True)
                    result.exit_code = child.exitstatus if child.exitstatus is not None else child.status
                except Exception:  # noqa: BLE001
                    pass
            result.error_message = str(exc)
            if not result.combined_output:
                result.combined_output = ""
        finally:
            if stdout_path and stdout_path.exists():
                result.stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
            if stderr_path and stderr_path.exists():
                result.stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
            if not result.combined_output:
                result.combined_output = result.stdout + result.stderr
            result.finished_at = datetime.now()
            self._persist_log(result)

        return result

    def _persist_log(self, result: CommandResult) -> None:
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            safe_name = result.session_name.replace("/", "_").replace(" ", "_")
            filename = f"{result.started_at.strftime('%Y-%m-%d_%H-%M-%S')}_{safe_name}.log"
            log_path = self.log_dir / filename
            log_path.write_text(result.as_log_text(), encoding="utf-8")
            result.log_path = str(log_path)
        except Exception:  # noqa: BLE001
            result.log_path = None

    def _create_session_dir(self) -> Path:
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            return Path(tempfile.mkdtemp(prefix="session_", dir=self.state_dir))
        except Exception:  # noqa: BLE001
            return Path(tempfile.mkdtemp(prefix="session_"))
