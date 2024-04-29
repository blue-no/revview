from typing import Literal

from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QPushButton


def apply_button_style(
    button: QPushButton,
    theme: Literal["primary", "secondary"] = "primary",
) -> None:

    if theme == "primary":
        args = [
            "QPushButton {",
            "height: 26px;",
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
            "height: 26px;",
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
        "font-size: 14pt;",
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
            "height: 22px;",
            "font-size: 16px;",
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
            "height: 22px;",
            "font-size: 16px;",
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
