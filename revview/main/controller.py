from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from revview._const import _settings_file
from revview._style import (
    apply_button_style,
    apply_icon_button_style,
    apply_lineedit_style,
)
from revview.main.model import (
    BaseImage,
    DifferenceDetection,
    ImageFactory,
    Page,
)
from revview.main.view import Ui_MainWindow
from revview.settings.controller import SettingsDialogController
from revview.settings.model import Settings


@dataclass
class PagePixmap:
    data: QtGui.QPixmap

    @classmethod
    def from_ndarray(cls, image: np.ndarray) -> PagePixmap:
        h, w = image.shape[:2]
        data = QtGui.QPixmap(
            QtGui.QImage(
                image.data,
                w,
                h,
                3 * w,
                QtGui.QImage.Format_RGB888,
            )
        )
        return PagePixmap(data=data)

    def resize(self, height: int, width: int) -> PagePixmap:
        data = self.data.scaled(
            width,
            height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        return PagePixmap(data=data)


class MainWindowController:

    def __init__(
        self,
        settings: Settings,
        parent_window: QtWidgets.QMainWindow | None = None,
    ) -> None:
        self.window = QtWidgets.QMainWindow(parent=parent_window)
        self.settings = settings
        self.image_factory = ImageFactory()
        self.ui = self._setup_ui(window=self.window)

        self.diffview = DifferenceView(
            parent_window=self.window,
            slideLbl_l=self.ui.slideLbl_L,
            slideLbl_r=self.ui.slideLbl_R,
            sizeLbl_l=self.ui.sizeLbl_L,
            sizeLbl_r=self.ui.sizeLbl_R,
            detection=DifferenceDetection(settings=settings),
        )

        self.page_l = PageTurning(
            total_lbl=self.ui.totpageLbl_L,
            page_le=self.ui.pageLE_L,
            first_btn=self.ui.firstBtn_L,
            prev_btn=self.ui.prevBtn_L,
            next_btn=self.ui.nextBtn_L,
            last_btn=self.ui.lastBtn_L,
            update_func=self.diffview.update_left,
        )
        self.page_r = PageTurning(
            total_lbl=self.ui.totpageLbl_R,
            page_le=self.ui.pageLE_R,
            first_btn=self.ui.firstBtn_R,
            prev_btn=self.ui.prevBtn_R,
            next_btn=self.ui.nextBtn_R,
            last_btn=self.ui.lastBtn_R,
            update_func=self.diffview.update_right,
        )
        self.page_sync = SyncPageTurning(
            page_l=self.page_l,
            page_r=self.page_r,
            first_btn=self.ui.firstBtn_sync,
            prev_btn=self.ui.prevBtn_sync,
            next_btn=self.ui.nextBtn_sync,
            last_btn=self.ui.lastBtn_sync,
        )

        self.ui.fileBtn_L.clicked.connect(
            lambda: self._set_image_pages_with_dialog(
                fp_le=self.ui.fpLE_L,
                page_tgt=self.page_l,
                page_ref=self.page_r,
            )
        )
        self.ui.fileBtn_R.clicked.connect(
            lambda: self._set_image_pages_with_dialog(
                fp_le=self.ui.fpLE_R,
                page_tgt=self.page_r,
                page_ref=self.page_l,
            )
        )
        self.ui.slideLbl_L.dragEnterEvent = self._validate_file_type
        self.ui.slideLbl_L.dropEvent = (
            lambda event: self._set_image_pages_with_filedrop(
                event=event,
                fp_le=self.ui.fpLE_L,
                page_tgt=self.page_l,
                page_ref=self.page_r,
            )
        )
        self.ui.slideLbl_R.dragEnterEvent = self._validate_file_type
        self.ui.slideLbl_R.dropEvent = (
            lambda event: self._set_image_pages_with_filedrop(
                event=event,
                fp_le=self.ui.fpLE_R,
                page_tgt=self.page_r,
                page_ref=self.page_r,
            )
        )

        self.ui.pageLE_L.setValidator(QtGui.QIntValidator(bottom=1))
        self.ui.pageLE_R.setValidator(QtGui.QIntValidator(bottom=1))

        self.ui.pageLE_L.enterEvent = lambda _: self._show_slide_no(
            page=self.page_l,
            page_le=self.ui.pageLE_L,
        )
        self.ui.pageLE_R.enterEvent = lambda _: self._show_slide_no(
            page=self.page_r,
            page_le=self.ui.pageLE_R,
        )
        self.ui.settingsBtn.clicked.connect(
            lambda: SettingsDialogController(
                settings=self.settings,
                parent_window=self.window,
                change_callback=self.diffview.update_view,
            ).show_window()
        )

        self.page_l.disable()
        self.page_r.disable()
        self.page_sync.disable()

        self._register_key_event(self.window)

    def show_window(self) -> None:
        self.window.show()

    def _setup_ui(self, window: QtWidgets.QMainWindow) -> Ui_MainWindow:
        ui = Ui_MainWindow()
        ui.setupUi(window)

        if self.settings.apply_mdesign:
            apply_icon_button_style(ui.fileBtn_L)
            apply_icon_button_style(ui.fileBtn_R)
            apply_icon_button_style(ui.settingsBtn)
            apply_button_style(ui.firstBtn_L, theme="primary")
            apply_button_style(ui.firstBtn_R, theme="primary")
            apply_button_style(ui.firstBtn_sync, theme="secondary")
            apply_button_style(ui.prevBtn_L, theme="primary")
            apply_button_style(ui.prevBtn_R, theme="primary")
            apply_button_style(ui.prevBtn_sync, theme="secondary")
            apply_button_style(ui.nextBtn_L, theme="primary")
            apply_button_style(ui.nextBtn_R, theme="primary")
            apply_button_style(ui.nextBtn_sync, theme="secondary")
            apply_button_style(ui.lastBtn_L, theme="primary")
            apply_button_style(ui.lastBtn_R, theme="primary")
            apply_button_style(ui.lastBtn_sync, theme="secondary")
            apply_lineedit_style(ui.fpLE_L, theme="secondary")
            apply_lineedit_style(ui.fpLE_R, theme="secondary")
            apply_lineedit_style(ui.pageLE_L, theme="primary")
            apply_lineedit_style(ui.pageLE_R, theme="primary")

        return ui

    def _register_key_event(self, widget: QtWidgets.QWidget) -> None:
        def key_event(event: QtGui.QKeyEvent) -> None:
            key = event.key()
            if key == Qt.Key_PageUp:
                self.page_sync.go_prev_page()
            elif key == Qt.Key_PageDown:
                self.page_sync.go_next_page()
            elif key == Qt.Key_Home:
                self.page_sync.go_first_page()
            elif key == Qt.Key_End:
                self.page_sync.go_last_page()

        widget.keyPressEvent = key_event

    def _validate_file_type(self, event: QtGui.QDragEnterEvent) -> None:
        if not event.mimeData().hasUrls:
            event.ignore()
            return
        urls = event.mimeData().urls()
        if len(urls) > 1:
            event.ignore()
            return
        fp = Path(urls[0].toLocalFile())
        if fp.suffix.lower() not in self.image_factory.supported_suffs():
            event.ignore()
            return
        event.accept()

    def _set_image_pages_with_filedrop(
        self,
        event: QtGui.QDropEvent,
        fp_le: QtWidgets.QLineEdit,
        page_tgt: PageTurning,
        page_ref: PageTurning,
    ) -> None:
        fp = Path(event.mimeData().urls()[0].toLocalFile())

        self._set_image_pages(
            fp=fp,
            fp_le=fp_le,
            page_tgt=page_tgt,
            page_ref=page_ref,
        )

    def _set_image_pages_with_dialog(
        self,
        fp_le: QtWidgets.QLineEdit,
        page_tgt: PageTurning,
        page_ref: PageTurning,
    ) -> None:
        fp = self._select_file()
        if fp is None:
            return

        self._set_image_pages(
            fp=fp,
            fp_le=fp_le,
            page_tgt=page_tgt,
            page_ref=page_ref,
        )

    def _set_image_pages(
        self,
        fp: Path,
        fp_le: QtWidgets.QLineEdit,
        page_tgt: PageTurning,
        page_ref: PageTurning,
    ) -> None:

        suff = Path(fp).suffix
        page_cls = self.image_factory.create(type_=suff)

        img = page_cls.open(fp=fp)
        pbar = QtWidgets.QProgressDialog(
            "読み込み中...",
            "キャンセル",
            0,
            img.total,
            parent=self.window,
        )
        pbar.setWindowTitle("RevView")
        img.load_pages(callback=lambda i: pbar.setValue(i + 1))
        page_tgt.load_image(img=img)
        pbar.close()

        fp_le.setText(fp.as_posix())
        page_tgt.go_first_page()
        page_tgt.enable()
        if page_ref.is_loaded():
            self.page_sync.enable()

    def _show_slide_no(
        self,
        page: PageTurning,
        page_le: QtWidgets.QLineEdit,
    ) -> None:
        if not page_le.text().isdecimal():
            page_le.setText(str(page.curpage))
            return
        page.go_page_no(p=int(page_le.text()))

    def _select_file(self) -> Path | None:
        ftypes = " ".join(
            ["*" + s for s in self.image_factory.supported_suffs()]
        )
        dialog = QtWidgets.QFileDialog(
            caption="ファイルを開く",
            filter=f"ファイル ({ftypes})",
            directory=self.settings.last_folder,
        )
        if dialog.exec_():
            fp = Path(dialog.selectedFiles()[0])
            self.settings.last_folder = fp.parent.as_posix()
            self.settings.write(fp=_settings_file)
            return fp
        return None


class DifferenceView:

    def __init__(
        self,
        parent_window: QtWidgets.QMainWindow,
        slideLbl_l: QtWidgets.QLabel,
        slideLbl_r: QtWidgets.QLabel,
        sizeLbl_l: QtWidgets.QLabel,
        sizeLbl_r: QtWidgets.QLabel,
        detection: DifferenceDetection,
    ) -> None:
        self.parent_window = parent_window
        self.slide_lbl_l = slideLbl_l
        self.slide_lbl_r = slideLbl_r
        self.size_lbl_l = sizeLbl_l
        self.size_lbl_r = sizeLbl_r
        self.detection = detection

        self.slide_lbl_l.resizeEvent = lambda _: self._set_view_left()
        self.slide_lbl_r.resizeEvent = lambda _: self._set_view_right()

        self.page_l: Page | None = None
        self.page_r: Page | None = None
        self.pixmap_l: PagePixmap | None = None
        self.pixmap_r: PagePixmap | None = None

    def update_left(self, page: Page) -> None:
        self.page_l = page
        self.update_view()

    def update_right(self, page: Page) -> None:
        self.page_r = page
        self.update_view()

    def update_view(self) -> None:
        if self.page_l is not None:
            self.pixmap_l = PagePixmap.from_ndarray(self.page_l.data)
            self._set_view_left()
        if self.page_r is not None:
            self.pixmap_r = PagePixmap.from_ndarray(self.page_r.data)
            self._set_view_right()
        if self.page_r is None or self.page_l is None:
            return
        if self.page_l.size == self.page_r.size:
            data_l, data_r = self.detection.difference(
                src1=self.page_l.data,
                src2=self.page_r.data,
            )
            self.pixmap_l = PagePixmap.from_ndarray(data_l)
            self.pixmap_r = PagePixmap.from_ndarray(data_r)

        self._set_view_left()
        self._set_view_right()

    def _set_view_left(self) -> None:
        if self.pixmap_l is None:
            return
        self._set_view(
            page_tgt=self.page_l,
            page_ref=self.page_r,
            pixmap=self.pixmap_l,
            slide_label=self.slide_lbl_l,
            size_label=self.size_lbl_l,
        )

    def _set_view_right(self) -> None:
        if self.pixmap_r is None:
            return
        self._set_view(
            page_tgt=self.page_r,
            page_ref=self.page_l,
            pixmap=self.pixmap_r,
            slide_label=self.slide_lbl_r,
            size_label=self.size_lbl_r,
        )

    def _set_view(
        self,
        page_tgt: Page,
        page_ref: Page,
        pixmap: PagePixmap,
        slide_label: QtWidgets.QLabel,
        size_label: QtWidgets.QLabel,
    ) -> None:
        slide_label.setPixmap(
            pixmap.resize(
                width=slide_label.width(),
                height=slide_label.height(),
            ).data
        )

        w_tgt, h_tgt = page_tgt.size
        if page_ref is not None:
            w_ref, h_ref = page_ref.size
        else:
            w_ref, h_ref = w_tgt, h_tgt

        if w_tgt != w_ref or h_tgt != h_ref:
            size_label.setText(f"⚠ サイズ: {w_tgt} x {h_tgt}  ")
            size_label.setStyleSheet("QLabel { color: orange; }")
        else:
            size_label.setText(f"サイズ: {w_tgt} x {h_tgt}")
            size_label.setStyleSheet("QLabel { color: black; }")


class SyncPageTurning:

    def __init__(
        self,
        page_l: PageTurning,
        page_r: PageTurning,
        first_btn: QtWidgets.QPushButton,
        prev_btn: QtWidgets.QPushButton,
        next_btn: QtWidgets.QPushButton,
        last_btn: QtWidgets.QPushButton,
    ) -> None:
        self.page_l = page_l
        self.page_r = page_r
        self.first_btn = first_btn
        self.prev_btn = prev_btn
        self.next_btn = next_btn
        self.last_btn = last_btn

        self.first_btn.clicked.connect(self.go_first_page)
        self.last_btn.clicked.connect(self.go_last_page)
        self.prev_btn.clicked.connect(self.go_prev_page)
        self.next_btn.clicked.connect(self.go_next_page)

    def disable(self) -> None:
        self.first_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.last_btn.setEnabled(False)

    def enable(self) -> None:
        self.first_btn.setEnabled(True)
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.last_btn.setEnabled(True)

    def go_first_page(self) -> None:
        self.page_l.go_first_page()
        self.page_r.go_first_page()

    def go_last_page(self) -> None:
        self.page_l.go_last_page()
        self.page_r.go_last_page()

    def go_prev_page(self) -> None:
        self.page_l.go_prev_page()
        self.page_r.go_prev_page()

    def go_next_page(self) -> None:
        self.page_l.go_next_page()
        self.page_r.go_next_page()


class PageTurning:

    def __init__(
        self,
        total_lbl: QtWidgets.QLabel,
        page_le: QtWidgets.QLineEdit,
        first_btn: QtWidgets.QPushButton,
        prev_btn: QtWidgets.QPushButton,
        next_btn: QtWidgets.QPushButton,
        last_btn: QtWidgets.QPushButton,
        update_func: Callable[[Page], None],
    ) -> None:
        self.img = None
        self.total_lbl = total_lbl
        self.page_le = page_le
        self.first_btn = first_btn
        self.prev_btn = prev_btn
        self.next_btn = next_btn
        self.last_btn = last_btn
        self.update_func = update_func
        self.curpage = 0

        self.first_btn.clicked.connect(self.go_first_page)
        self.last_btn.clicked.connect(self.go_last_page)
        self.prev_btn.clicked.connect(self.go_prev_page)
        self.next_btn.clicked.connect(self.go_next_page)

    def is_loaded(self) -> bool:
        return self.img is not None

    def disable(self) -> None:
        self.page_le.setEnabled(False)
        self.first_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.last_btn.setEnabled(False)

    def enable(self) -> None:
        self.page_le.setEnabled(True)
        self.first_btn.setEnabled(True)
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.last_btn.setEnabled(True)

    def load_image(self, img: BaseImage) -> None:
        self.img = img
        self.total_lbl.setText(str(self.img.total))

    def go_first_page(self) -> None:
        if self.img is None:
            return
        self.curpage = 1
        img = self.img.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_last_page(self) -> None:
        if self.img is None:
            return
        self.curpage = self.img.total
        img = self.img.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_prev_page(self) -> None:
        if self.img is None:
            return
        self.curpage = self._within_page_range(self.curpage - 1)
        img = self.img.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_next_page(self) -> None:
        if self.img is None:
            return
        self.curpage = self._within_page_range(self.curpage + 1)
        img = self.img.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_page_no(self, p: int) -> None:
        if self.img is None:
            return
        self.curpage = self._within_page_range(p)
        img = self.img.get_page(p=self.curpage)
        self.update_func(img)

    def _within_page_range(self, p: int) -> int:
        return min(max(p, 1), self.img.total)
