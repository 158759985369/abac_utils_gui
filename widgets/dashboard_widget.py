from __future__ import annotations

from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.command_result import CommandResult
from repositories.status_probe import StatusProbe
from utils.message_helper import command_result_to_text


class DashboardWidget(QWidget):
    def __init__(self, probe: StatusProbe) -> None:
        super().__init__()
        self.probe = probe

        self.platform_label = QLabel("-")
        self.root_label = QLabel("-")
        self.abac_label = QLabel("-")
        self.config_label = QLabel("-")
        self.kernel_label = QLabel("-")
        self.shared_label = QLabel("-")
        self.service_table = QTableWidget(0, 3)
        self.service_table.setHorizontalHeaderLabels(["Service", "Active", "Enabled"])
        self.last_result_box = QPlainTextEdit()
        self.last_result_box.setReadOnly(True)

        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.clicked.connect(self.refresh_view)

        status_group = QGroupBox("System Status")
        status_form = QFormLayout(status_group)
        status_form.addRow("Platform", self.platform_label)
        status_form.addRow("Root", self.root_label)
        status_form.addRow("abac CLI", self.abac_label)
        status_form.addRow("/etc/abac", self.config_label)
        status_form.addRow("/sys/kernel/security/abac", self.kernel_label)
        status_form.addRow("/home/secured", self.shared_label)

        service_group = QGroupBox("systemd Services")
        service_layout = QVBoxLayout(service_group)
        service_layout.addWidget(self.service_table)

        result_group = QGroupBox("Recent Command Result")
        result_layout = QVBoxLayout(result_group)
        result_layout.addWidget(self.last_result_box)

        top_bar = QHBoxLayout()
        top_bar.addWidget(refresh_button)
        top_bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(top_bar)
        layout.addWidget(status_group)
        layout.addWidget(service_group)
        layout.addWidget(result_group, stretch=1)

        self.refresh_view()

    def refresh_view(self) -> None:
        snapshot = self.probe.snapshot()
        self.platform_label.setText(str(snapshot["platform"]))
        self.root_label.setText("yes" if snapshot["is_root"] else "no")
        self.abac_label.setText(str(snapshot["abac_cli"] or "not found"))
        self.config_label.setText("ready" if snapshot["config_root_exists"] else "missing")
        self.kernel_label.setText("ready" if snapshot["kernel_root_exists"] else "missing")
        self.shared_label.setText("ready" if snapshot["shared_dir_exists"] else "missing")

        services = snapshot["service_statuses"]
        self.service_table.setRowCount(len(services))
        for row, (name, info) in enumerate(services.items()):
            self.service_table.setItem(row, 0, QTableWidgetItem(name))
            self.service_table.setItem(row, 1, QTableWidgetItem(info["active"]))
            self.service_table.setItem(row, 2, QTableWidgetItem(info["enabled"]))
        self.service_table.resizeColumnsToContents()

    def set_last_result(self, result: CommandResult | None) -> None:
        if result is None:
            self.last_result_box.setPlainText("No command has been executed yet.")
            return
        self.last_result_box.setPlainText(command_result_to_text(result))

