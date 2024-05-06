from __future__ import annotations

from typing import Literal

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QPushButton,
)


def rgb_to_hex(code: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*code)


def hex_to_rgb(code: str) -> tuple[int, int, int]:
    return tuple(int(code[i : i + 2], 16) for i in range(0, 6, 2))


def change_brightness(code: tuple[int, int, int], ratio: float) -> None:
    return tuple(int(i * ratio) for i in code)


def apply_button_style(
    button: QPushButton,
    theme: Literal["primary", "secondary"] = "primary",
) -> None:

    if theme == "primary":
        args = [
            "QPushButton {",
            "height: 28px;",
            "width: 105px;",
            "border-radius: 4px;",
            "border-style: none;",
            "color: black;",
            "background-color: rgb(255, 255, 255);",
            "}",
            "QPushButton:hover {",
            "background-color: rgb(245, 245, 245);",
            "}",
            "QPushButton:pressed{",
            "background-color: rgb(235, 235, 235);",
            "}",
        ]
    elif theme == "secondary":
        args = [
            "QPushButton {",
            "height: 28px;",
            "width: 105px;",
            "border-radius: 4px;",
            "border-style: none;",
            "color: white;",
            "background-color: rgb(30, 136, 229);",
            "}",
            "QPushButton:hover {",
            "background-color: rgb(25, 118, 210);",
            "}",
            "QPushButton:pressed{",
            "background-color: rgb(21, 101, 192);",
            "}",
        ]
    else:
        raise NotImplementedError

    shadow = QGraphicsDropShadowEffect(
        offset=QPoint(1, 1),
        blurRadius=10,
        color=QColor(200, 200, 200),
    )

    button.setStyleSheet("".join(args))
    button.setGraphicsEffect(shadow)


def apply_icon_button_style(button: QPushButton) -> None:

    args = [
        "QPushButton {",
        "font-size: 12pt;",
        "height: 40px;",
        "width: 45px;",
        "border-radius: 4px;",
        "border-style: none;",
        "}",
        "QPushButton:hover {",
        "background-color: rgb(225, 225, 225);",
        "}",
        "QPushButton:pressed{",
        "background-color: rgb(215, 215, 215);",
        "}",
    ]

    button.setStyleSheet("".join(args))


def apply_lineedit_style(
    lineedit: QLineEdit,
    theme: Literal["primary", "secondary"] = "primary",
) -> None:
    if theme == "primary":
        args = [
            "QLineEdit {",
            "height: 24px;",
            "font-size: 18px;",
            "border-radius: 4px;",
            "border-style: solid;",
            "border-width: 2px;",
            "border-color : rgb(255, 255, 255) rgb(255, 255, 255)",
            "rgb(140, 140, 140) rgb(255, 255, 255);",
            "background-color: rgb(255, 255, 255);",
            "}",
        ]
    elif theme == "secondary":
        args = [
            "QLineEdit {",
            "height: 28px;",
            "font-size: 18px;",
            "border-radius: 4px;",
            "border-style: solid;",
            "border-width: 2px;",
            "border-color : rgb(255, 255, 255) rgb(255, 255, 255)",
            "rgb(21, 101, 192) rgb(255, 255, 255);",
            "background-color: rgb(255, 255, 255);",
            "}",
        ]
    else:
        raise NotImplementedError

    lineedit.setStyleSheet("".join(args))


def apply_droppable_label_style(
    label: QLabel,
    theme: Literal["normal", "hover"],
) -> None:
    if theme == "normal":
        args = [
            "QLabel {",
            "font-family: Meiryo UI;",
            "background-color: rgb(230, 230, 230);",
            "}",
        ]
    elif theme == "hover":
        args = [
            "QLabel {",
            "font-family: Meiryo UI;",
            "border-style: solid;",
            "border-width: 2px;",
            "border-color: rgb(21, 101, 192);",
            "background-color: rgb(220, 220, 220);",
            "}",
        ]
    else:
        raise NotImplementedError

    label.setStyleSheet("".join(args))


def apply_warning_label_style(
    label: QLabel,
    theme: Literal["normal", "warn"],
) -> None:
    if theme == "normal":
        args = [
            "QLabel {",
            "font-family: Meiryo UI;",
            "color: black;",
            "}",
        ]
    elif theme == "warn":
        args = [
            "QLabel {",
            "font-family: Meiryo UI;",
            "color: orange;",
            "}",
        ]
    else:
        raise NotImplementedError

    label.setStyleSheet("".join(args))


def apply_color_picker_button_style(
    button: QPushButton,
    color: tuple[int, int, int],
) -> None:
    args = [
        "QPushButton {",
        "border-radius: 5px;",
        "border-style: solid;",
        "border-color: lightgray;",
        "border-width: 1px;",
        f"background-color: {rgb_to_hex(color)};",
        "}",
    ]

    button.setStyleSheet("".join(args))
