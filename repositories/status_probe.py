from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


class StatusProbe:
    def __init__(
        self,
        config_root: str = "/etc/abac",
        kernel_root: str = "/sys/kernel/security/abac",
        shared_dir: str = "/home/secured",
    ) -> None:
        self.config_root = Path(config_root)
        self.kernel_root = Path(kernel_root)
        self.shared_dir = Path(shared_dir)
        self.services = ["abac.service", "abac_watch.service", "abac_env.service"]

    def snapshot(self) -> dict[str, object]:
        data = {
            "platform": platform.system(),
            "is_linux": platform.system() == "Linux",
            "is_root": hasattr(os, "geteuid") and os.geteuid() == 0,
            "abac_cli": shutil.which("abac"),
            "config_root_exists": self.config_root.exists(),
            "kernel_root_exists": self.kernel_root.exists(),
            "shared_dir_exists": self.shared_dir.exists(),
            "service_statuses": {},
        }
        service_statuses: dict[str, dict[str, str]] = {}
        for service in self.services:
            service_statuses[service] = self._probe_service(service)
        data["service_statuses"] = service_statuses
        return data

    def _probe_service(self, service_name: str) -> dict[str, str]:
        return {
            "active": self._systemctl("is-active", service_name),
            "enabled": self._systemctl("is-enabled", service_name),
        }

    def _systemctl(self, action: str, service_name: str) -> str:
        try:
            completed = subprocess.run(
                ["systemctl", action, service_name],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as exc:  # noqa: BLE001
            return f"unavailable ({exc})"
        output = (completed.stdout or completed.stderr).strip()
        return output or f"exit {completed.returncode}"

