from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np
import win32com.client
from PIL import Image


@contextmanager
def open_presentation(fp: Path | str) -> Any:
    fp = Path(fp)
    if not fp.exists():
        raise FileNotFoundError

    app = win32com.client.Dispatch("Powerpoint.Application")
    prs = app.Presentations.Open(
        fp.absolute().as_posix(),
        ReadOnly=True,
        Untitled=False,
        WithWindow=False,
    )
    try:
        yield prs
    finally:
        app.Quit()


class ImageFactory:

    def __init__(self) -> None:
        self.clses = {
            ".pptx": PPTImage,
            ".tiff": TiffImage,
        }

    def create(self, type_: str) -> BaseImage:
        return self.clses[type_]()


class BaseImage:
    def __init__(self) -> None:
        self.pages: list[np.ndarray]
        self.total: int

    def open(self, fp: Path | str) -> BaseImage:
        raise NotImplementedError

    def load_pages(self, callback: Callable[[int], None] | None = None) -> None:
        raise NotImplementedError

    def get_page(self, p: int) -> np.ndarray:
        raise NotImplementedError


class PPTImage(BaseImage):

    def __init__(self) -> None:
        self.pages: list[np.ndarray] = []
        self.total: int = 0
        self._tmp_wd: Path = Path(__file__).parent.joinpath(".tmp")
        self._suff: str = "jpg"
        self._prs: win32com.client.CDispatch | None = None

    def open(self, fp: Path | str) -> PPTImage:
        with open_presentation(fp=fp) as prs:
            self._prs = prs
            self.total = len(prs.Slides)
        return self

    def load_pages(self, callback: Callable[[int], None] | None = None) -> None:
        self._tmp_wd.mkdir(parents=True, exist_ok=True)
        pages_ = []
        for i, slide in enumerate(self._prs.Slides, start=1):
            img_fn = Path(str(i).zfill(4)).with_suffix("." + self._suff.lower())
            img_fp = self._tmp_wd / img_fn
            slide.Export(img_fp.absolute(), self._suff.upper())

            img = cv2.imread(img_fp.as_posix())
            pages_.append(img)

            img_fp.unlink(missing_ok=True)

            if callback is not None:
                callback(i)

        self.pages = pages_
        self._prs.Close()

    def get_page(self, p: int) -> np.ndarray:
        return self.pages[p - 1]


class TiffImage(BaseImage):

    def __init__(self) -> None:
        self.pages: list[np.ndarray] = []
        self.total: int = 0
        self._img: Image.Image | None = None

    def open(self, fp: Path | str) -> TiffImage:
        self._img = Image.open(fp)
        self.total = self._img.n_frames
        return self

    def load_pages(self, callback: Callable[[int], None] | None = None) -> None:
        pages_ = []
        for i in range(self._img.n_frames):
            self._img.seek(i)
            pages_.append(
                cv2.cvtColor(np.array(self._img.copy()), cv2.COLOR_RGB2BGR)
            )

            if callback is not None:
                callback(i)

        self.pages = pages_

    def get_page(self, p: int) -> np.ndarray:
        return self.pages[p - 1]


class DifferenceDetection:

    def __init__(
        self,
        line_color: tuple[int] = (0, 0, 0),
        line_width: int = 1,
        bg_color: tuple[int] = None,
    ) -> None:
        self._line_bgr = line_color[::-1]
        self._line_width = line_width
        self._bg_bgr = None if bg_color is None else list(bg_color[::-1])
        self._min_cnt_area = 10
        self._bg_del_margin = 20
        self._n_merge_mask = 2
        self._extend_mergin = 1

    def difference(
        self,
        src1: np.ndarray,
        src2: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        if not self._image_same_size(src1=src1, src2=src2):
            return (src1, src2)
        mask = self._mask_diff_area(src1=src1, src2=src2)
        cnts1 = self._extract_merged_mask_contour(
            src=src1,
            mask=mask,
            n_repeat=self._n_merge_mask,
        )
        cnts2 = self._extract_merged_mask_contour(
            src=src2,
            mask=mask,
            n_repeat=self._n_merge_mask,
        )
        dst1 = self._draw_output_contour(src=src1, cnts=cnts1)
        dst2 = self._draw_output_contour(src=src2, cnts=cnts2)

        return (dst1, dst2)

    def _image_same_size(self, src1: np.ndarray, src2: np.ndarray) -> bool:
        return src1.shape == src2.shape

    def _mask_diff_area(
        self,
        src1: np.ndarray,
        src2: np.ndarray,
    ) -> np.ndarray:
        gray1 = cv2.cvtColor(src1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(src2, cv2.COLOR_BGR2GRAY)
        diff = np.abs(gray1.astype(np.int64) - gray2.astype(np.int64)).astype(
            np.uint8
        )
        mask = cv2.threshold(diff, 1, 255, cv2.THRESH_BINARY)[1]
        return mask

    def _extract_merged_mask_contour(
        self,
        src: np.ndarray,
        mask: np.ndarray,
        n_repeat: int = 1,
    ) -> Any:
        cnts = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )[0]

        for _ in range(n_repeat):
            dmask = self._draw_contours(
                src=src,
                dst=np.zeros_like(src),
                cnts=cnts,
                color=(255, 255, 255),
                width=-1,
                min_area=self._min_cnt_area,
                bg_bgr=self._bg_bgr,
                bg_del_margin=self._bg_del_margin,
                extend_margin=self._extend_mergin,
            )
            dgray = cv2.cvtColor(dmask, cv2.COLOR_BGR2GRAY)
            cnts = cv2.findContours(
                dgray,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_NONE,
            )[0]
        return cnts

    def _draw_output_contour(
        self,
        src: np.ndarray,
        cnts: list[Any],
    ) -> np.ndarray:
        dst = self._draw_contours(
            src=src,
            cnts=cnts,
            dst=src.copy(),
            color=self._line_bgr,
            width=self._line_width,
        )
        return dst

    def _draw_contours(
        self,
        src: np.ndarray,
        dst: np.ndarray,
        cnts: list[Any],
        color: tuple[int, int, int],
        width: int = 1,
        min_area: int = 0,
        bg_bgr: tuple[int, int, int] | None = None,
        bg_del_margin: int = 0,
        extend_margin: int = 0,
    ) -> np.ndarray:
        for cnt in cnts:
            if cv2.contourArea(cnt) < min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            if bg_bgr is not None:
                x1, x2 = x, x + w
                y1, y2 = y, y + h
                if w > 2 * bg_del_margin:
                    x1, x2 = x1 + bg_del_margin, x2 - bg_del_margin
                if h > 2 * bg_del_margin:
                    y1, y2 = y1 + bg_del_margin, y2 - bg_del_margin
                if np.all(src[y1:y2, x1:x2] == list(bg_bgr)):
                    continue

            cv2.rectangle(
                dst,
                (x - extend_margin, y - extend_margin),
                (x + w + extend_margin, y + h + extend_margin),
                color,
                width,
            )
        return dst
