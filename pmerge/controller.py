from __future__ import annotations

import sys
from typing import Callable

import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pmerge.model import DifferenceDetection, ImagePPT, open_presentation
from pmerge.view import Ui_MainWindow


def ndarray_to_pixmap(image: np.ndarray) -> QtGui.QPixmap:
    height, width, _ = image.shape
    return QtGui.QPixmap(
        QtGui.QImage(
            image.data,
            width,
            height,
            3 * width,
            QtGui.QImage.Format_RGB888,
        ).rgbSwapped()
    )


class MainWindowController:
    inst: MainWindowController
    root: QtWidgets.QMainWindow

    def __init__(self, ui: Ui_MainWindow) -> None:
        self.diff = DifferenceView(
            slideLbl_l=ui.slideLbl_L,
            slideLbl_r=ui.slideLbl_R,
        )

        self.file_btn_l = ui.fileBtn_L
        self.file_btn_r = ui.fileBtn_R
        self.fp_le_l = ui.fpLE_L
        self.fp_le_r = ui.fpLE_R

        self.page_l = PageTurning(
            total_lbl=ui.totpageLbl_L,
            page_le=ui.pageLE_L,
            first_btn=ui.firstBtn_L,
            prev_btn=ui.prevBtn_L,
            next_btn=ui.nextBtn_L,
            last_btn=ui.lastBtn_L,
            update_func=self.diff.update_left,
        )
        self.page_r = PageTurning(
            total_lbl=ui.totpageLbl_R,
            page_le=ui.pageLE_R,
            first_btn=ui.firstBtn_R,
            prev_btn=ui.prevBtn_R,
            next_btn=ui.nextBtn_R,
            last_btn=ui.lastBtn_R,
            update_func=self.diff.update_right,
        )
        self.page_sync = SyncPageTurning(
            page_l=self.page_l,
            page_r=self.page_r,
            first_btn=ui.firstBtn_sync,
            prev_btn=ui.prevBtn_sync,
            next_btn=ui.nextBtn_sync,
            last_btn=ui.lastBtn_sync,
        )

        self.file_btn_l.clicked.connect(
            lambda: self.select_ppt(
                fp_le=self.fp_le_l,
                page_tgt=self.page_l,
                page_ref=self.page_r,
            )
        )
        self.file_btn_r.clicked.connect(
            lambda: self.select_ppt(
                fp_le=self.fp_le_r,
                page_tgt=self.page_r,
                page_ref=self.page_l,
            )
        )
        ui.pageLE_L.setValidator(QtGui.QIntValidator(bottom=1))
        ui.pageLE_R.setValidator(QtGui.QIntValidator(bottom=1))

        ui.pageLE_L.enterEvent = lambda _: self.show_slide_no(
            page=self.page_l,
            page_le=ui.pageLE_L,
        )
        ui.pageLE_R.enterEvent = lambda _: self.show_slide_no(
            page=self.page_r,
            page_le=ui.pageLE_R,
        )

        self.page_l.disable()
        self.page_r.disable()
        self.page_sync.disable()

    @classmethod
    def run(cls: MainWindowController) -> None:
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        ui = Ui_MainWindow()
        ui.setupUi(window)
        cls.inst = cls(ui=ui)
        cls.root = window
        window.show()
        sys.exit(app.exec_())

    def select_ppt(
        self,
        fp_le: QtWidgets.QLineEdit,
        page_tgt: PageTurning,
        page_ref: PageTurning,
    ) -> None:
        fp = self._select_pptfile()
        if fp is None:
            return

        with open_presentation(fp=fp) as prs:
            pbar = QtWidgets.QProgressDialog(
                "読み込み中...",
                "キャンセル",
                0,
                len(prs.Slides),
                parent=self.root,
            )
            page_tgt.load_imageppt(
                ppt=ImagePPT().load(
                    slides=prs.Slides,
                    callback=lambda i: pbar.setValue(i + 1),
                )
            )
        pbar.close()

        fp_le.setText(fp)
        page_tgt.go_first_page()
        page_tgt.enable()
        if page_ref.is_loaded():
            self.page_sync.enable()

    def show_slide_no(
        self,
        page: PageTurning,
        page_le: QtWidgets.QLineEdit,
    ) -> None:
        if not page_le.text().isdecimal():
            page_le.setText(str(page.curpage))
            return
        page.go_page_no(p=int(page_le.text()))

    def _select_pptfile(self) -> str | None:
        dialog = QtWidgets.QFileDialog(
            caption="ファイルを開く",
            filter="PowerPoint プレゼンテーション (*.pptx)",
        )
        if dialog.exec_():
            return dialog.selectedFiles()[0]
        return None


class DifferenceView:

    def __init__(
        self,
        slideLbl_l: QtWidgets.QLabel,
        slideLbl_r: QtWidgets.QLabel,
    ) -> None:
        self.slide_lbl_l = slideLbl_l
        self.slide_lbl_r = slideLbl_r

        self.slide_lbl_l.resizeEvent = lambda _: self.set_resized_pixmap_left()
        self.slide_lbl_r.resizeEvent = lambda _: self.set_resized_pixmap_right()

        self.img_l: np.ndarray | None = None
        self.img_r: np.ndarray | None = None
        self.pixmap_l: QtGui.QPixmap | None = None
        self.pixmap_r: QtGui.QPixmap | None = None

        self.det = DifferenceDetection(
            line_color=(255, 128, 0),
            line_width=3,
            bg_color=(255, 255, 255),
        )

    def update_left(self, img: np.ndarray) -> None:
        self.img_l = img
        self._update_view()

    def update_right(self, img: np.ndarray) -> None:
        self.img_r = img
        self._update_view()

    def _update_view(self) -> None:
        if self.img_r is None:
            self.pixmap_l = ndarray_to_pixmap(self.img_l)
            self.set_resized_pixmap_left()
            return
        if self.img_l is None:
            self.pixmap_r = ndarray_to_pixmap(self.img_r)
            self.set_resized_pixmap_right()
            return

        dimg_l, dimg_r = self.det.difference(src1=self.img_l, src2=self.img_r)
        self.pixmap_l = ndarray_to_pixmap(dimg_l)
        self.pixmap_r = ndarray_to_pixmap(dimg_r)
        self.set_resized_pixmap_left()
        self.set_resized_pixmap_right()

    def set_resized_pixmap_left(self) -> None:
        self._set_resized_pixmap(
            self.slide_lbl_l,
            self.pixmap_l,
        )

    def set_resized_pixmap_right(self) -> None:
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
        self.ppt = None
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
        return self.ppt is not None

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

    def load_imageppt(self, ppt: ImagePPT) -> None:
        self.ppt = ppt
        self.total_lbl.setText(str(self.ppt.total))

    def go_first_page(self) -> None:
        self.curpage = 1
        img = self.ppt.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_last_page(self) -> None:
        self.curpage = self.ppt.total
        img = self.ppt.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_prev_page(self) -> None:
        self.curpage = self._within_page_range(self.curpage - 1)
        img = self.ppt.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_next_page(self) -> None:
        self.curpage = self._within_page_range(self.curpage + 1)
        img = self.ppt.get_page(p=self.curpage)
        self.page_le.setText(str(self.curpage))
        self.update_func(img)

    def go_page_no(self, p: int) -> None:
        self.curpage = self._within_page_range(p)
        img = self.ppt.get_page(p=self.curpage)
        self.update_func(img)

    def _within_page_range(self, p: int) -> int:
        return min(max(p, 1), self.ppt.total)
