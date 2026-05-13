from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QGroupBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from services.runtime_service import RuntimeService
from services.systemd_service import SystemdService
from utils.message_helper import command_result_to_text, dict_to_pretty_lines
from widgets.services_widget import ServicesWidget


class RuntimeWidget(QWidget):
    def __init__(
        self,
        runtime_service: RuntimeService,
        systemd_service: SystemdService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.runtime_service = runtime_service
        self.execute_command = execute_command

        self.snapshot_box = QPlainTextEdit()
        self.snapshot_box.setReadOnly(True)
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)
        self.services_widget = ServicesWidget(systemd_service, execute_command)

        load_button = QPushButton("Run abac load")
        load_button.clicked.connect(self._run_load)
        refresh_button = QPushButton("Refresh Runtime Status")
        refresh_button.clicked.connect(self.refresh_view)

        runtime_group = QGroupBox("Runtime Snapshot")
        runtime_layout = QVBoxLayout(runtime_group)
        runtime_layout.addWidget(load_button)
        runtime_layout.addWidget(refresh_button)
        runtime_layout.addWidget(self.snapshot_box)

        result_group = QGroupBox("Load Session Output")
        result_layout = QVBoxLayout(result_group)
        result_layout.addWidget(self.result_box)

        layout = QVBoxLayout(self)
        layout.addWidget(runtime_group)
        layout.addWidget(self.services_widget)
        layout.addWidget(result_group, stretch=1)

        self.refresh_view()

    def refresh_view(self) -> None:
        snapshot = self.runtime_service.snapshot()
        self.snapshot_box.setPlainText(dict_to_pretty_lines(snapshot))
        self.services_widget.refresh_view()

    def _run_load(self) -> None:
        self.execute_command(self.runtime_service.load, self._handle_result)

    def _handle_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        self.refresh_view()

