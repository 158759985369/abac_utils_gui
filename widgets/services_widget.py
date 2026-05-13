from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from services.systemd_service import SystemdService
from utils.message_helper import command_result_to_text


class ServicesWidget(QWidget):
    def __init__(
        self,
        service: SystemdService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.service = service
        self.execute_command = execute_command

        self.service_combo = QComboBox()
        self.service_combo.addItems(self.service.probe.services)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["start", "stop", "restart"])
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Service", "Active", "Enabled"])

        form_group = QGroupBox("systemctl Control")
        form = QFormLayout(form_group)
        form.addRow("Service", self.service_combo)
        form.addRow("Action", self.action_combo)
        run_button = QPushButton("Execute systemctl")
        run_button.clicked.connect(self._submit)
        form.addRow("", run_button)

        refresh_button = QPushButton("Refresh Services")
        refresh_button.clicked.connect(self.refresh_view)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Service writes on this page go through real `systemctl` calls."))
        layout.addWidget(form_group)
        layout.addWidget(refresh_button)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("Session Output"))
        layout.addWidget(self.result_box, stretch=1)

        self.refresh_view()

    def refresh_view(self) -> None:
        snapshot = self.service.snapshot()["service_statuses"]
        self.table.setRowCount(len(snapshot))
        for row, (name, info) in enumerate(snapshot.items()):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(info["active"]))
            self.table.setItem(row, 2, QTableWidgetItem(info["enabled"]))
        self.table.resizeColumnsToContents()

    def _submit(self) -> None:
        service_name = self.service_combo.currentText()
        action = self.action_combo.currentText()
        self.execute_command(lambda: self.service.run_action(service_name, action), self._handle_result)

    def _handle_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        self.refresh_view()

