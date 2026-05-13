from __future__ import annotations

from PyQt5.QtCore import QSettings


class Preferences:
    def __init__(self) -> None:
        self.settings = QSettings("abac_gui", "abac_gui")

    def save_geometry(self, widget) -> None:
        self.settings.setValue("window_geometry", widget.saveGeometry())

    def restore_geometry(self, widget) -> None:
        geometry = self.settings.value("window_geometry")
        if geometry is not None:
            widget.restoreGeometry(geometry)
