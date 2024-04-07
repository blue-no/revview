from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
import win32com.client


class ImagePPT:

    def __init__(self, fp: Path | str) -> None:
        self._tmp_wd: Path = Path(__file__).parent.joinpath(".tmp")
        self.slides: list[np.ndarray] = []
        self.total: int = 0
        self.ftype: str = "jpg"

        self._load(fp=fp)

    def _load(self, fp: Path | str) -> None:
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

        self._tmp_wd.mkdir(parents=True, exist_ok=True)
        self._empty_wd()

        self._save_slides_as_image(prs=prs)
        prs.Close()
        app.Quit()
        self._load_slide_imgages()

        self._empty_wd()
        self._tmp_wd.rmdir()

    def get_page(self, p: int) -> np.ndarray:
        return self.slides[p - 1]

    def _save_slides_as_image(self, prs: Any) -> None:
        for i, slide in enumerate(prs.Slides, start=1):
            out_fp = Path(str(i).zfill(4)).with_suffix("." + self.ftype.lower())
            slide.Export(
                (self._tmp_wd / out_fp).absolute(),
                self.ftype.upper(),
            )

        self.total = i

    def _load_slide_imgages(self) -> None:
        slides = []
        for fp in self._tmp_wd.iterdir():
            img = cv2.imread(fp.as_posix())
            slides.append(img)

        self.slides = slides

    def _empty_wd(self) -> None:
        for fp in self._tmp_wd.iterdir():
            fp.unlink(missing_ok=True)


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

    def difference(
        self,
        src1: np.ndarray,
        src2: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        if not self._image_same_size(src1=src1, src2=src2):
            return (src1, src2)
        mask = self._mask_diff_area(src1=src1, src2=src2)
        cnts1 = self._extract_contours(src=src1, mask=mask)
        cnts2 = self._extract_contours(src=src2, mask=mask)
        dst1 = self._draw_contours(src=src1, cnts=cnts1)
        dst2 = self._draw_contours(src=src2, cnts=cnts2)
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
        diff = np.abs(gray1.astype(np.int64) - gray2.astype(np.int64)).astype(np.uint8)
        mask = cv2.threshold(diff, 1, 255, cv2.THRESH_BINARY)[1]
        return mask

    def _extract_contours(
        self,
        src: np.ndarray,
        mask: np.ndarray,
    ) -> np.ndarray:

        dmy = np.zeros_like(src)
        cnts_dmy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
        for cnt in cnts_dmy:
            if cv2.contourArea(cnt) < self._min_cnt_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if self._bg_bgr is not None:
                x1, x2 = x + self._bg_del_margin, x + w - self._bg_del_margin
                y1, y2 = y + self._bg_del_margin, y + h - self._bg_del_margin
                if (
                    x2 - x1 > 0
                    and y2 - y1 > 0
                    and np.all(src[y1:y2, x1:x2] == list(self._bg_bgr))
                ):
                    continue
            cv2.rectangle(dmy, (x, y), (x + w, y + h), (255, 255, 255), -1)
        mask_dmy = cv2.cvtColor(dmy, cv2.COLOR_BGR2GRAY)
        cnts = cv2.findContours(mask_dmy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
        return cnts

    def _draw_contours(
        self,
        src: np.ndarray,
        cnts: list[np.ndarray],
    ) -> np.ndarray:
        dst = src.copy()
        for cnt in cnts:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(
                dst,
                (x, y),
                (x + w, y + h),
                self._line_bgr,
                self._line_width,
            )
        return dst
