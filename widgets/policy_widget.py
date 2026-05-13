from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
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
from repositories.policy_repository import PolicyRepository
from services.policy_service import PolicyService
from utils.message_helper import command_result_to_text


class PolicyWidget(QWidget):
    def __init__(
        self,
        service: PolicyService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.service = service
        self.execute_command = execute_command
        self.user_combos: dict[str, QComboBox] = {}
        self.obj_combos: dict[str, QComboBox] = {}
        self.env_combos: dict[str, QComboBox] = {}

        self.rules_box = QPlainTextEdit()
        self.rules_box.setReadOnly(True)
        self.preview_box = QPlainTextEdit()
        self.preview_box.setReadOnly(True)
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)

        self.user_form = QFormLayout()
        self.obj_form = QFormLayout()
        self.env_form = QFormLayout()
        self.op_combo = QComboBox()
        self.op_combo.addItems(["READ", "MODIFY"])
        self.op_combo.currentTextChanged.connect(self._update_preview)
        self.delete_combo = QComboBox()

        add_group = QGroupBox("Add Policy Rule")
        add_layout = QVBoxLayout(add_group)
        user_group = QGroupBox("User Attributes")
        user_group.setLayout(self.user_form)
        obj_group = QGroupBox("Object Attributes")
        obj_group.setLayout(self.obj_form)
        env_group = QGroupBox("Environment Attributes")
        env_group.setLayout(self.env_form)
        add_layout.addWidget(user_group)
        add_layout.addWidget(obj_group)
        add_layout.addWidget(env_group)
        op_form = QFormLayout()
        op_form.addRow("Operation", self.op_combo)
        add_layout.addLayout(op_form)
        preview_button = QPushButton("Refresh Preview")
        preview_button.clicked.connect(self._update_preview)
        add_button = QPushButton("Run abac policy add")
        add_button.clicked.connect(self._submit_add)
        add_layout.addWidget(preview_button)
        add_layout.addWidget(add_button)
        add_layout.addWidget(QLabel("Rule Preview"))
        add_layout.addWidget(self.preview_box)

        delete_group = QGroupBox("Delete Rule")
        delete_form = QFormLayout(delete_group)
        delete_form.addRow("Rule Index", self.delete_combo)
        delete_button = QPushButton("Run abac policy delete")
        delete_button.clicked.connect(self._submit_delete)
        delete_form.addRow("", delete_button)

        top_row = QHBoxLayout()
        top_row.addWidget(add_group, stretch=3)
        top_row.addWidget(delete_group, stretch=1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addWidget(QLabel("Current Rules"))
        layout.addWidget(self.rules_box, stretch=1)
        layout.addWidget(QLabel("Session Output"))
        layout.addWidget(self.result_box, stretch=1)

        self.refresh_view()

    def refresh_view(self) -> None:
        rules = self.service.list_rules()
        avps = self.service.avp_repository.load()
        self.rules_box.setPlainText(
            "\n".join(f"[{index}] {PolicyRepository.render_rule(rule)}" for index, rule in enumerate(rules))
            or "<no rules>"
        )
        self.delete_combo.clear()
        for index, rule in enumerate(rules):
            self.delete_combo.addItem(f"{index}: {PolicyRepository.render_rule(rule)}", index)

        self._rebuild_section_form(self.user_form, self.user_combos, avps["user"])
        self._rebuild_section_form(self.obj_form, self.obj_combos, avps["obj"])
        self._rebuild_section_form(self.env_form, self.env_combos, avps["env"])
        self._update_preview()

    def _rebuild_section_form(
        self,
        form: QFormLayout,
        store: dict[str, QComboBox],
        avps: dict[str, list[str]],
    ) -> None:
        while form.rowCount():
            form.removeRow(0)
        store.clear()
        for name, values in avps.items():
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(values)
            combo.currentTextChanged.connect(self._update_preview)
            store[name] = combo
            form.addRow(name, combo)

    def _submit_add(self) -> None:
        try:
            user_selections = self._collect_prefix_section(self.user_combos, allow_empty=False)
            obj_selections = self._collect_prefix_section(self.obj_combos, allow_empty=False)
            env_selections = self._collect_prefix_section(self.env_combos, allow_empty=True)
        except ValueError as exc:
            self.result_box.setPlainText(str(exc))
            return

        operation = "R" if self.op_combo.currentText() == "READ" else "M"
        self.execute_command(
            lambda: self.service.add(user_selections, obj_selections, env_selections, operation),
            self._handle_result,
        )

    def _submit_delete(self) -> None:
        index = self.delete_combo.currentData()
        if index is None:
            self.result_box.setPlainText("No policy rule is available for deletion.")
            return
        rule_label = self.delete_combo.currentText()
        answer = QMessageBox.question(
            self,
            "Confirm Policy Deletion",
            f"Delete the selected policy rule?\n\n{rule_label}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.result_box.setPlainText("Policy deletion cancelled.")
            return
        self.execute_command(lambda: self.service.delete(int(index)), self._handle_result)

    def _handle_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        self.refresh_view()

    def _update_preview(self) -> None:
        try:
            user = self._collect_prefix_section(self.user_combos, allow_empty=False, strict=False)
            obj = self._collect_prefix_section(self.obj_combos, allow_empty=False, strict=False)
            env = self._collect_prefix_section(self.env_combos, allow_empty=True, strict=False)
        except ValueError as exc:
            self.preview_box.setPlainText(str(exc))
            return
        rule = {
            "user": user,
            "obj": obj,
            "env": env,
            "op": self.op_combo.currentText(),
        }
        self.preview_box.setPlainText(PolicyRepository.render_rule(rule))

    def _collect_prefix_section(
        self,
        combos: dict[str, QComboBox],
        allow_empty: bool,
        strict: bool = True,
    ) -> dict[str, str]:
        selections: dict[str, str] = {}
        blank_seen = False
        for name, combo in combos.items():
            value = combo.currentText()
            if not value:
                blank_seen = True
                continue
            if blank_seen:
                raise ValueError(
                    "Policy selections must follow the CLI prompt order. Fill earlier attributes before later ones."
                )
            selections[name] = value
        if strict and not allow_empty and not selections:
            raise ValueError("User and object sections each require at least one attribute selection.")
        return selections
