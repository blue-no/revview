from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from revview.main.model import BaseImage, DifferenceDetection, ImageFactory
from revview.main.view import Ui_MainWindow
from revview.settings.controller import SettingsDialogController
from revview.settings.model import Settings


def ndarray_to_pixmap(image: np.ndarray) -> QtGui.QPixmap:
    height, width, _ = image.shape
    return QtGui.QPixmap(
        QtGui.QImage(
            image.data,
            width,
            height,
            3 * width,
            QtGui.QImage.Format_RGB888,
        )
    )


class MainWindowController:

    def __init__(
        self,
        settings: Settings,
        parent_window: QtWidgets.QMainWindow | None = None,
    ) -> None:
        self.window = QtWidgets.QMainWindow(parent=parent_window)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.window)

        self.settings = settings
        self.image_factory = ImageFactory()

        self.diffview = DifferenceView(
            slideLbl_l=self.ui.slideLbl_L,
            slideLbl_r=self.ui.slideLbl_R,
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
            lambda: self._set_image_pages(
                fp_le=self.ui.fpLE_L,
                page_tgt=self.page_l,
                page_ref=self.page_r,
            )
        )
        self.ui.fileBtn_R.clicked.connect(
            lambda: self._set_image_pages(
                fp_le=self.ui.fpLE_R,
                page_tgt=self.page_r,
                page_ref=self.page_l,
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

    def _register_key_event(self, widget: QtWidgets.QWidget):
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

    def _set_image_pages(
        self,
        fp_le: QtWidgets.QLineEdit,
        page_tgt: PageTurning,
        page_ref: PageTurning,
    ) -> None:
        fp = self._select_file()
        if fp is None:
            return

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

        fp_le.setText(fp)
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

    def _select_file(self) -> str | None:
        ftypes = " ".join(
            ["*" + s for s in self.image_factory.supported_suffs()]
        )
        dialog = QtWidgets.QFileDialog(
            caption="ファイルを開く",
            filter=f"ファイル ({ftypes})",
        )
        if dialog.exec_():
            return dialog.selectedFiles()[0]
        return None


class DifferenceView:

    def __init__(
        self,
        slideLbl_l: QtWidgets.QLabel,
        slideLbl_r: QtWidgets.QLabel,
        detection: DifferenceDetection,
    ) -> None:
        self.slide_lbl_l = slideLbl_l
        self.slide_lbl_r = slideLbl_r
        self.detection = detection

        self.slide_lbl_l.resizeEvent = lambda _: self._set_resized_pixmap_left()
        self.slide_lbl_r.resizeEvent = (
            lambda _: self._set_resized_pixmap_right()
        )

        self.img_l: np.ndarray | None = None
        self.img_r: np.ndarray | None = None
        self.pixmap_l: QtGui.QPixmap | None = None
        self.pixmap_r: QtGui.QPixmap | None = None

    def update_left(self, img: np.ndarray) -> None:
        self.img_l = img
        self.update_view()

    def update_right(self, img: np.ndarray) -> None:
        self.img_r = img
        self.update_view()

    def update_view(self) -> None:
        if self.img_r is None and self.img_l is None:
            return
        if self.img_r is None:
            self.pixmap_l = ndarray_to_pixmap(self.img_l)
            self._set_resized_pixmap_left()
            return
        if self.img_l is None:
            self.pixmap_r = ndarray_to_pixmap(self.img_r)
            self._set_resized_pixmap_right()
            return

        dimg_l, dimg_r = self.detection.difference(
            src1=self.img_l, src2=self.img_r
        )
        self.pixmap_l = ndarray_to_pixmap(dimg_l)
        self.pixmap_r = ndarray_to_pixmap(dimg_r)
        self._set_resized_pixmap_left()
        self._set_resized_pixmap_right()

    def _set_resized_pixmap_left(self) -> None:
        self._set_resized_pixmap(
            self.slide_lbl_l,
            self.pixmap_l,
        )

    def _set_resized_pixmap_right(self) -> None:
        self._set_resized_pixmap(
            self.slide_lbl_r,
            self.pixmap_r,
        )

    def _set_resized_pixmap(
        self,
        label: QtWidgets.QLabel,
        pixmap: QtGui.QPixmap,
    ) -> None:
        if pixmap is None:
            return
        label.setPixmap(
            pixmap.scaled(
                label.width(),
                label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )


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
        update_func: Callable[[np.ndarray], None],
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
