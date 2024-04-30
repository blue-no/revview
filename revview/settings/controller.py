from __future__ import annotations

from typing import Callable

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from revview._const import _settings_file
from revview.settings.model import Settings, rgb_to_hex
from revview.settings.view import Ui_SettingsDialog


class SettingsDialogController:
    _window: QtWidgets.QMainWindow | None = None

    def __init__(
        self,
        settings: Settings,
        parent_window: QtWidgets.QMainWindow | None = None,
        change_callback: Callable | None = None,
    ) -> None:
        if SettingsDialogController._window is None:
            self.window = QtWidgets.QMainWindow(parent=parent_window)
            SettingsDialogController._window = self.window
        else:
            self.window = SettingsDialogController._window
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self.window)

        self.settings = settings
        self.change_callback = change_callback

        self.ui.lineColorBtn.clicked.connect(lambda: self._set_line_color())
        self.ui.lineWidthSB.valueChanged.connect(lambda: self._set_line_width())
        self.ui.bgColorBtn.clicked.connect(lambda: self._set_bg_color())
        self.ui.ignoreBgCB.stateChanged.connect(
            lambda state: self._switch_ignore_bg(state=state)
        )
        self.ui.applyMDesignCB.stateChanged.connect(
            lambda state: self._switch_mdesign(state=state)
        )

        self._set_button_style(
            button=self.ui.lineColorBtn,
            background_color=settings.line_color,
        )
        self._set_button_style(
            button=self.ui.bgColorBtn,
            background_color=settings.bg_color,
        )
        self.ui.lineWidthSB.setValue(settings.line_width)
        self.ui.ignoreBgCB.setChecked(settings.ignore_bg_rect)
        self.ui.applyMDesignCB.setChecked(settings.apply_legacy)
        self._update()

    def show_window(self) -> None:
        if self.window.isVisible():
            return
        self.window.show()

    def _set_line_color(self) -> None:
        rgb = self._select_color_with_dialog()
        if rgb is None:
            return
        self._set_button_style(
            button=self.ui.lineColorBtn, background_color=rgb
        )
        self.settings.line_color = rgb
        self._update()

    def _set_line_width(self) -> None:
        self.settings.line_width = self.ui.lineWidthSB.value()
        self._update()

    def _set_bg_color(self) -> None:
        rgb = self._select_color_with_dialog()
        if rgb is None:
            return
        self._set_button_style(button=self.ui.bgColorBtn, background_color=rgb)
        self.settings.bg_color = rgb
        self._update()

    def _switch_ignore_bg(self, state: Qt.CheckState) -> None:
        self.settings.ignore_bg_rect = state == Qt.Checked
        self._update()

    def _switch_mdesign(self, state: Qt.CheckState) -> None:
        self.settings.apply_legacy = state == Qt.Checked
        self._update()

    def _update(self) -> None:
        if self.change_callback is not None:
            self.change_callback()
        self.settings.write(fp=_settings_file)

    def _select_color_with_dialog(self) -> None:
        color = QtWidgets.QColorDialog(parent=self.window).getColor()
        if not color.isValid():
            return None
        rgb = color.getRgb()[:3]
        return rgb

    def _set_button_style(
        self,
        button: QtWidgets.QPushButton,
        background_color: tuple[int, int, int],
    ) -> None:
        args = [
            "QPushButton {",
            "border-radius: 5px;",
            "border-style: solid;",
            "border-color: lightgray;",
            "border-width: 1px;",
            f"background-color: {rgb_to_hex(background_color)};",
            "}",
        ]

        button.setStyleSheet("".join(args))
