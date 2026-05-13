from __future__ import annotations

import os
import platform
from typing import Callable

from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from core.command_result import CommandResult
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder
from core.task_worker import TaskWorker
from repositories.avp_repository import AvpRepository
from repositories.object_repository import ObjectRepository
from repositories.policy_repository import PolicyRepository
from repositories.status_probe import StatusProbe
from repositories.user_repository import UserRepository
from services.avp_service import AvpService
from services.init_service import InitService
from services.object_service import ObjectService
from services.policy_service import PolicyService
from services.runtime_service import RuntimeService
from services.systemd_service import SystemdService
from services.user_service import UserService
from utils.preferences import Preferences
from widgets.avp_widget import AvpWidget
from widgets.dashboard_widget import DashboardWidget
from widgets.init_widget import InitWidget
from widgets.object_widget import ObjectWidget
from widgets.policy_widget import PolicyWidget
from widgets.runtime_widget import RuntimeWidget
from widgets.user_widget import UserWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ABAC GUI")
        self.resize(1400, 900)
        self.preferences = Preferences()
        self.last_result: CommandResult | None = None
        self._workers: list[TaskWorker] = []

        runner = InteractiveRunner()
        builder = SessionBuilder()
        probe = StatusProbe()
        avp_repository = AvpRepository()
        user_repository = UserRepository()
        object_repository = ObjectRepository()
        policy_repository = PolicyRepository()

        init_service = InitService(runner, builder)
        avp_service = AvpService(runner, builder, avp_repository)
        user_service = UserService(runner, builder, user_repository, avp_repository)
        object_service = ObjectService(runner, builder, object_repository, avp_repository)
        policy_service = PolicyService(runner, builder, policy_repository, avp_repository)
        runtime_service = RuntimeService(runner, builder, probe)
        systemd_service = SystemdService(runner, builder, probe)

        self.dashboard = DashboardWidget(probe)
        self.init_page = InitWidget(init_service, self.execute_command)
        self.avp_page = AvpWidget(avp_service, self.execute_command)
        self.user_page = UserWidget(user_service, self.execute_command)
        self.object_page = ObjectWidget(object_service, self.execute_command)
        self.policy_page = PolicyWidget(policy_service, self.execute_command)
        self.runtime_page = RuntimeWidget(runtime_service, systemd_service, self.execute_command)

        self.page_order = [
            ("Dashboard", self.dashboard),
            ("Initialize", self.init_page),
            ("AVP", self.avp_page),
            ("Users", self.user_page),
            ("Objects", self.object_page),
            ("Policies", self.policy_page),
            ("Runtime & Services", self.runtime_page),
        ]

        self.nav_list = QListWidget()
        for name, _page in self.page_order:
            self.nav_list.addItem(name)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        self.stack = QStackedWidget()
        for _name, page in self.page_order:
            self.stack.addWidget(page)

        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.addWidget(self.nav_list, stretch=1)
        shell_layout.addWidget(self.stack, stretch=5)
        self.setCentralWidget(shell)
        self.nav_list.setCurrentRow(0)
        self.dashboard.set_last_result(None)
        self.refresh_all()
        self.preferences.restore_geometry(self)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.preferences.save_geometry(self)
        super().closeEvent(event)

    def _switch_page(self, index: int) -> None:
        if index >= 0:
            self.stack.setCurrentIndex(index)

    def execute_command(
        self,
        task: Callable[[], object],
        on_done: Callable[[CommandResult], None] | None = None,
    ) -> None:
        worker = TaskWorker(task)
        self._workers.append(worker)
        self.statusBar().showMessage("Running command...")

        def handle_success(payload: object) -> None:
            if not isinstance(payload, CommandResult):
                self.statusBar().showMessage("Command finished with unexpected payload.", 5000)
                return
            self.last_result = payload
            self.dashboard.set_last_result(payload)
            self.refresh_all()
            if on_done is not None:
                on_done(payload)
            if payload.success:
                self.statusBar().showMessage(payload.short_summary(), 5000)
            else:
                self.statusBar().showMessage(payload.short_summary(), 10000)
                QMessageBox.warning(self, "Command Failed", payload.short_summary())

        def handle_failure(message: str) -> None:
            self.statusBar().showMessage("Background task failed.", 10000)
            QMessageBox.critical(self, "Task Error", message)

        def handle_finish() -> None:
            if worker in self._workers:
                self._workers.remove(worker)
            worker.deleteLater()

        worker.succeeded.connect(handle_success)
        worker.failed.connect(handle_failure)
        worker.finished.connect(handle_finish)
        worker.start()

    def refresh_all(self) -> None:
        self.dashboard.refresh_view()
        self.dashboard.set_last_result(self.last_result)
        self.user_page.refresh_view()
        self.avp_page.refresh_view()
        self.object_page.refresh_view()
        self.policy_page.refresh_view()
        self.runtime_page.refresh_view()


def runtime_guard_message() -> str | None:
    if platform.system() != "Linux":
        return "ABAC GUI only supports Linux target environments."
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        return "请以 root 权限启动本程序"
    return None


def run() -> int:
    app = QApplication([])
    message = runtime_guard_message()
    if message:
        QMessageBox.critical(None, "ABAC GUI", message)
        return 1
    window = MainWindow()
    window.show()
    return app.exec_()

