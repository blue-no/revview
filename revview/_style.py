from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QLineEdit, QPushButton


def apply_button_style(button: QPushButton) -> None:

    args = [
        "QPushButton {",
        "height: 28px;",
        "width: 105px;",
        "border-radius: 4px;",
        "border-style: none;",
        "background-color: rgb(255, 255, 255);",
        "}",
        "QPushButton:hover {",
        "background-color: rgb(250, 250, 250);",
        "}",
        "QPushButton:pressed{",
        "background-color: rgb(240, 240, 240);",
        "}",
    ]

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
        "height: 45px;",
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


def apply_lineedit_style(lineedit: QLineEdit) -> None:

    args = [
        "QLineEdit {",
        "height: 20px;",
        "border-radius: 4px;",
        "border-style: solid;",
        "border-width: 2px;",
        "border-color : rgb(255, 255, 255) rgb(255, 255, 255)",
        "rgb(140, 140, 140) rgb(255, 255, 255);",
        "background-color: rgb(255, 255, 255);",
        "}",
    ]

    lineedit.setStyleSheet("".join(args))
