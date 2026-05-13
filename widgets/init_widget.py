from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from services.init_service import InitService
from utils.message_helper import command_result_to_text


class InitWidget(QWidget):
    def __init__(
        self,
        service: InitService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.service = service
        self.execute_command = execute_command
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)

        intro = QLabel("Use this page only for environment checks and `abac init` / `abac init --force`.")
        intro.setWordWrap(True)

        init_button = QPushButton("Run abac init")
        init_button.clicked.connect(lambda: self._run(False))
        force_button = QPushButton("Run abac init --force")
        force_button.clicked.connect(lambda: self._run(True))

        button_row = QHBoxLayout()
        button_row.addWidget(init_button)
        button_row.addWidget(force_button)
        button_row.addStretch(1)

        result_group = QGroupBox("Session Output")
        result_layout = QVBoxLayout(result_group)
        result_layout.addWidget(self.result_box)

        layout = QVBoxLayout(self)
        layout.addWidget(intro)
        layout.addLayout(button_row)
        layout.addWidget(result_group, stretch=1)

    def _run(self, force: bool) -> None:
        if force:
            answer = QMessageBox.warning(
                self,
                "Confirm Force Initialization",
                "This will overwrite the existing ABAC config under /etc/abac and remove current attributes and rules. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                self.result_box.setPlainText("Force initialization cancelled.")
                return
        self.execute_command(lambda: self.service.initialize(force=force), self._handle_result)

    def _handle_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))

    def refresh_view(self) -> None:
        return
