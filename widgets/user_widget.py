from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from services.user_service import UserService
from utils.message_helper import command_result_to_text


class UserWidget(QWidget):
    def __init__(
        self,
        service: UserService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.service = service
        self.execute_command = execute_command
        self.attr_inputs: dict[str, QComboBox] = {}

        self.user_box = QPlainTextEdit()
        self.user_box.setReadOnly(True)
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)

        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.attr_form = QFormLayout()

        add_group = QGroupBox("Add User")
        add_layout = QVBoxLayout(add_group)
        top_form = QFormLayout()
        top_form.addRow("Username", self.username_edit)
        top_form.addRow("Password", self.password_edit)
        top_form.addRow("Confirm Password", self.confirm_password_edit)
        add_layout.addLayout(top_form)
        add_layout.addLayout(self.attr_form)
        add_button = QPushButton("Run abac user add")
        add_button.clicked.connect(self._submit_add)
        add_layout.addWidget(add_button)

        self.delete_combo = QComboBox()
        delete_button = QPushButton("Run abac user delete")
        delete_button.clicked.connect(self._submit_delete)
        delete_group = QGroupBox("Delete User")
        delete_form = QFormLayout(delete_group)
        delete_form.addRow("Existing User", self.delete_combo)
        delete_form.addRow("", delete_button)

        top_row = QHBoxLayout()
        top_row.addWidget(add_group, stretch=2)
        top_row.addWidget(delete_group, stretch=1)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("User creation keeps the CLI interaction order and sends passwords through the session runner."))
        layout.addLayout(top_row)
        layout.addWidget(QLabel("Current Users"))
        layout.addWidget(self.user_box, stretch=1)
        layout.addWidget(QLabel("Session Output"))
        layout.addWidget(self.result_box, stretch=1)

        self.refresh_view()

    def refresh_view(self) -> None:
        users = self.service.list_users()
        avps = self.service.avp_repository.load()["user"]

        self.user_box.setPlainText(
            "\n".join(
                f"{row['username']} ({row['uid']}): "
                + ", ".join(f"{key}={value}" for key, value in dict(row["avps"]).items())
                + (" [missing from system]" if not row["exists_in_system"] else "")
                for row in users
            )
            or "<no users>"
        )

        self.delete_combo.clear()
        for row in users:
            self.delete_combo.addItem(str(row["username"]))

        while self.attr_form.rowCount():
            self.attr_form.removeRow(0)
        self.attr_inputs.clear()
        for name, values in avps.items():
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(values)
            self.attr_inputs[name] = combo
            self.attr_form.addRow(f"{name}", combo)

    def _submit_add(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        selections = {name: combo.currentText() for name, combo in self.attr_inputs.items() if combo.currentText()}
        if not username:
            self.result_box.setPlainText("Username is required.")
            return
        if not password:
            self.result_box.setPlainText("Password is required.")
            return
        if password != confirm_password:
            self.result_box.setPlainText("Password confirmation does not match.")
            return
        if not selections:
            self.result_box.setPlainText("At least one user attribute selection is required.")
            return

        self.execute_command(lambda: self.service.add(username, selections, password), self._handle_add_result)

    def _submit_delete(self) -> None:
        username = self.delete_combo.currentText().strip()
        if not username:
            self.result_box.setPlainText("No user is available for deletion.")
            return
        answer = QMessageBox.question(
            self,
            "Confirm User Deletion",
            f"Delete Linux user and ABAC metadata for '{username}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.result_box.setPlainText("User deletion cancelled.")
            return
        self.execute_command(lambda: self.service.delete(username), self._handle_delete_result)

    def _handle_add_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        if result.success:
            self.password_edit.clear()
            self.confirm_password_edit.clear()
        self.refresh_view()

    def _handle_delete_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        self.refresh_view()
