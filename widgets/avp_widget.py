from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from services.avp_service import AvpService
from utils.message_helper import command_result_to_text


class AvpWidget(QWidget):
    def __init__(
        self,
        service: AvpService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.service = service
        self.execute_command = execute_command

        self.entity_type_combo = QComboBox()
        self.entity_type_combo.addItems(["user", "obj"])
        self.action_combo = QComboBox()
        self.action_combo.addItems(["add", "modify", "delete"])
        self.action_combo.currentTextChanged.connect(self._sync_form_state)
        self.name_edit = QLineEdit()
        self.values_edit = QLineEdit()
        self.values_edit.setPlaceholderText("example: role, level, zone")

        self.current_box = QPlainTextEdit()
        self.current_box.setReadOnly(True)
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)

        form_group = QGroupBox("Write Operation")
        form = QFormLayout(form_group)
        form.addRow("Entity Type", self.entity_type_combo)
        form.addRow("Action", self.action_combo)
        form.addRow("Attribute Name", self.name_edit)
        form.addRow("Comma Values", self.values_edit)

        run_button = QPushButton("Execute")
        run_button.clicked.connect(self._submit)
        refresh_button = QPushButton("Refresh AVPs")
        refresh_button.clicked.connect(self.refresh_view)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("All writes on this page go through `abac avp ...`."))
        layout.addWidget(form_group)
        layout.addWidget(run_button)
        layout.addWidget(refresh_button)
        layout.addWidget(QLabel("Current AVPs"))
        layout.addWidget(self.current_box, stretch=1)
        layout.addWidget(QLabel("Session Output"))
        layout.addWidget(self.result_box, stretch=1)

        self._sync_form_state()
        self.refresh_view()

    def refresh_view(self) -> None:
        avps = self.service.list_all()
        lines: list[str] = []
        for section in ("user", "obj", "env"):
            lines.append(f"[{section}]")
            if not avps[section]:
                lines.append("  <empty>")
            else:
                for name, values in avps[section].items():
                    lines.append(f"  {name}: {', '.join(values)}")
            lines.append("")
        self.current_box.setPlainText("\n".join(lines).strip())

    def _sync_form_state(self) -> None:
        is_delete = self.action_combo.currentText() == "delete"
        self.values_edit.setEnabled(not is_delete)

    def _submit(self) -> None:
        entity_type = self.entity_type_combo.currentText()
        action = self.action_combo.currentText()
        name = self.name_edit.text().strip()
        values = self.values_edit.text().strip()
        if not name:
            self.result_box.setPlainText("Attribute name is required.")
            return
        if action != "delete" and not values:
            self.result_box.setPlainText("Comma-separated values are required.")
            return

        if action == "add":
            task = lambda: self.service.add(entity_type, name, values)
        elif action == "modify":
            task = lambda: self.service.modify(entity_type, name, values)
        else:
            task = lambda: self.service.delete(entity_type, name)
        self.execute_command(task, self._handle_result)

    def _handle_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        self.refresh_view()

