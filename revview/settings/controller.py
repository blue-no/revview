from __future__ import annotations

from typing import Any, Callable

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from revview.settings.model import Settings, change_brightness, rgb_to_hex
from revview.settings.view import Ui_SettingsDialog


class SettingsDialogController:
    window: QtWidgets.QMainWindow | None = None

    def __init__(
        self,
        ui: Ui_SettingsDialog,
        settings: Settings,
        callback: Callable | None = None,
    ) -> None:
        self.ui = ui
        self.settings = settings
        self.callback = callback
        self.window.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.window.closeEvent = self.window_close_event
        ui.lineColorBtn.clicked.connect(lambda: self.set_line_color())
        ui.lineWidthSB.valueChanged.connect(lambda: self.set_line_width())
        ui.bgColorBtn.clicked.connect(lambda: self.set_bg_color())
        ui.ignoreBgCB.stateChanged.connect(
            lambda state: self.switch_ignore_bg(state=state)
        )

        self._set_button_style(
            button=ui.lineColorBtn,
            background_color=settings.line_color,
        )
        self._set_button_style(
            button=ui.bgColorBtn,
            background_color=settings.bg_color,
        )
        ui.lineWidthSB.setValue(settings.line_width)
        ui.ignoreBgCB.setChecked(settings.ignore_bg_rect)
        self.update()

    def window_close_event(self, event: Any) -> None:
        SettingsDialogController.window = None

    def set_line_color(self) -> None:
        color = QtWidgets.QColorDialog(parent=self.window).getColor()
        if not color.isValid():
            return
        rgb = color.getRgb()[:3]
        self._set_button_style(
            button=self.ui.lineColorBtn, background_color=rgb
        )
        self.settings.line_color = rgb
        self.update()

    def set_line_width(self) -> None:
        self.settings.line_width = self.ui.lineWidthSB.value()
        self.update()

    def set_bg_color(self) -> None:
        color = QtWidgets.QColorDialog(parent=self.window).getColor()
        if not color.isValid():
            return
        rgb = color.getRgb()[:3]
        self._set_button_style(button=self.ui.bgColorBtn, background_color=rgb)
        self.settings.bg_color = rgb
        self.update()

    def switch_ignore_bg(self, state: Qt.CheckState) -> None:
        self.settings.ignore_bg_rect = state == Qt.Checked
        self.update()

    def update(self) -> None:
        if self.callback is not None:
            self.callback()
        self.settings.write()

    def _set_button_style(
        self,
        button: QtWidgets.QPushButton,
        background_color: tuple[int, int, int],
    ) -> None:
        background_hex = rgb_to_hex(background_color)
        hover_hex = rgb_to_hex(change_brightness(background_color, ratio=0.9))
        args = [
            "QPushButton {",
            "border-radius: 5px;",
            "border-style: solid;",
            "border-color: lightgray;",
            "border-width: 1px;",
            f"background-color: {background_hex};",
            "}",
            "QPushButton:hover {",
            f"background-color: {hover_hex};",
            "}",
        ]

        button.setStyleSheet("".join(args))

    def _set_label_style(
        self,
        label: QtWidgets.QLabel,
        border_color: tuple[int, int, int],
        border_width: int,
        background_color: tuple[int, int, int],
    ) -> None:
        border_hex = rgb_to_hex(border_color)
        background_hex = rgb_to_hex(background_color)
        args = [
            "QLabel {",
            f"border: {border_width}px solid {border_hex};",
            f"background-color: {background_hex};",
            "}",
        ]

        label.setStyleSheet("".join(args))

    @classmethod
    def run(
        cls: SettingsDialogController,
        parent: QtWidgets.QWidget,
        settings: Settings,
        callback: Callable | None = None,
    ) -> None:
        if cls.window is not None:
            return
        window = QtWidgets.QMainWindow()
        ui = Ui_SettingsDialog()
        ui.setupUi(window)
        cls.window = window
        cls(
            ui=ui,
            settings=settings,
            callback=callback,
        )
        window.show()
