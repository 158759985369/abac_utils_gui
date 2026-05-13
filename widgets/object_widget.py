from __future__ import annotations

from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from services.object_service import ObjectService
from utils.message_helper import command_result_to_text


class ObjectWidget(QWidget):
    def __init__(
        self,
        service: ObjectService,
        execute_command: Callable[[Callable[[], object], Callable[[CommandResult], None] | None], None],
    ) -> None:
        super().__init__()
        self.service = service
        self.execute_command = execute_command

        self.entry_list = QListWidget()
        self.entry_list.currentTextChanged.connect(self._sync_object_view)
        self.attrs_box = QPlainTextEdit()
        self.attrs_box.setReadOnly(True)
        self.result_box = QPlainTextEdit()
        self.result_box.setReadOnly(True)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["add", "change", "delete"])
        self.action_combo.currentTextChanged.connect(self._sync_attribute_choices)
        self.attr_combo = QComboBox()
        self.attr_combo.currentTextChanged.connect(self._sync_value_choices)
        self.value_combo = QComboBox()

        form_group = QGroupBox("Write Operation")
        form = QFormLayout(form_group)
        form.addRow("Action", self.action_combo)
        form.addRow("Attribute", self.attr_combo)
        form.addRow("Value", self.value_combo)

        run_button = QPushButton("Execute abac obj")
        run_button.clicked.connect(self._submit)
        refresh_button = QPushButton("Refresh Shared Directory")
        refresh_button.clicked.connect(self.refresh_view)

        left = QVBoxLayout()
        left.addWidget(QLabel("/home/secured entries"))
        left.addWidget(self.entry_list, stretch=1)
        left.addWidget(refresh_button)

        right = QVBoxLayout()
        right.addWidget(QLabel("Selected Object Attributes"))
        right.addWidget(self.attrs_box, stretch=1)
        right.addWidget(form_group)
        right.addWidget(run_button)
        right.addWidget(QLabel("Session Output"))
        right.addWidget(self.result_box, stretch=1)

        layout = QHBoxLayout(self)
        layout.addLayout(left, stretch=2)
        layout.addLayout(right, stretch=3)

        self.refresh_view()

    def refresh_view(self) -> None:
        selected = self.entry_list.currentItem().text() if self.entry_list.currentItem() else ""
        entries = self.service.list_entries()
        self.entry_list.clear()
        self.entry_list.addItems(entries)
        if selected:
            matches = self.entry_list.findItems(selected, Qt.MatchExactly)
            if matches:
                self.entry_list.setCurrentItem(matches[0])
        if self.entry_list.count() and self.entry_list.currentRow() < 0:
            self.entry_list.setCurrentRow(0)
        self._sync_object_view()

    def _sync_object_view(self) -> None:
        object_path = self.current_object_path()
        attrs = self.service.get_attrs(object_path) if object_path else {}
        self.attrs_box.setPlainText(
            "\n".join(f"{name}={value}" for name, value in attrs.items()) or "<no attributes>"
        )
        self._sync_attribute_choices()

    def _sync_attribute_choices(self) -> None:
        object_path = self.current_object_path()
        current_attrs = self.service.get_attrs(object_path) if object_path else {}
        available = self.service.avp_repository.load()["obj"]
        action = self.action_combo.currentText()

        self.attr_combo.blockSignals(True)
        self.attr_combo.clear()
        if action == "add":
            names = [name for name in available if name not in current_attrs]
        else:
            names = list(current_attrs.keys())
        self.attr_combo.addItems(names)
        self.attr_combo.blockSignals(False)
        self._sync_value_choices()

    def _sync_value_choices(self) -> None:
        action = self.action_combo.currentText()
        attr_name = self.attr_combo.currentText()
        available = self.service.avp_repository.load()["obj"]

        self.value_combo.clear()
        self.value_combo.setEnabled(action != "delete")
        if action != "delete" and attr_name in available:
            self.value_combo.addItems(available[attr_name])

    def _submit(self) -> None:
        object_path = self.current_object_path()
        attr_name = self.attr_combo.currentText().strip()
        value = self.value_combo.currentText().strip()
        action = self.action_combo.currentText()

        if not object_path:
            self.result_box.setPlainText("Select an object under /home/secured first.")
            return
        if not attr_name:
            self.result_box.setPlainText("No valid attribute is available for this action.")
            return
        if action != "delete" and not value:
            self.result_box.setPlainText("A value must be selected.")
            return

        if action == "add":
            task = lambda: self.service.add(object_path, attr_name, value)
        elif action == "change":
            task = lambda: self.service.change(object_path, attr_name, value)
        else:
            task = lambda: self.service.delete(object_path, attr_name)
        self.execute_command(task, self._handle_result)

    def _handle_result(self, result: CommandResult) -> None:
        self.result_box.setPlainText(command_result_to_text(result))
        self.refresh_view()

    def current_object_path(self) -> str:
        item = self.entry_list.currentItem()
        return item.text() if item else ""
