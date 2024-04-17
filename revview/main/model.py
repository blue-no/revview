from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np
import win32com.client
from PIL import Image

from revview._const import _max_image_size
from revview.settings.model import Settings


def imread(fp: Path | str):
    fp = Path(fp)
    if not fp.is_file():
        raise FileNotFoundError
    b = np.fromfile(fp.as_posix(), dtype=np.uint8)
    return cv2.imdecode(b, cv2.IMREAD_COLOR)


def compress(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    hmax, wmax = _max_image_size
    if h <= hmax and w <= wmax:
        return image
    ratio = min(hmax / h, wmax / w)
    return cv2.resize(image, None, None, ratio, ratio)


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
        self.types = {
            ".pptx": PPTImage,
            ".ppt": PPTImage,
            ".tiff": TiffImage,
            ".tif": TiffImage,
        }

    def supported_suffs(self) -> list[str]:
        return self.types.keys()

    def create(self, type_: str) -> BaseImage:
        return self.types[type_.lower()]()


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
        super().__init__()
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

            img = imread(img_fp.as_posix())
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = compress(img)
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
        super().__init__()
        self._img: Image.Image | None = None

    def open(self, fp: Path | str) -> TiffImage:
        self._img = Image.open(fp)
        self.total = self._img.n_frames
        return self

    def load_pages(self, callback: Callable[[int], None] | None = None) -> None:
        pages_ = []
        for i in range(self._img.n_frames):
            self._img.seek(i)
            img = np.array(self._img.copy())
            if img.dtype == np.bool8:
                img = img.astype(dtype=np.uint8) * 255
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            img = compress(img)
            pages_.append(img)

            if callback is not None:
                callback(i)

        self.pages = pages_

    def get_page(self, p: int) -> np.ndarray:
        return self.pages[p - 1]


class DifferenceDetection:

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
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
        src1 = self._convert_to_color(src=src1)
        src2 = self._convert_to_color(src=src2)
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

    def _convert_to_color(self, src: np.ndarray) -> np.ndarray:
        n_ch = src.shape[-1]
        if n_ch == 3:
            return src
        return cv2.cvtColor(src, cv2.COLOR_GRAY2RGB)

    def _mask_diff_area(
        self,
        src1: np.ndarray,
        src2: np.ndarray,
    ) -> np.ndarray:
        gray1 = cv2.cvtColor(src1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(src2, cv2.COLOR_RGB2GRAY)
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
                bg_rgb=(
                    self.settings.bg_color
                    if self.settings.ignore_bg_rect
                    else None
                ),
                bg_del_margin=self._bg_del_margin,
                extend_margin=self._extend_mergin,
            )
            dgray = cv2.cvtColor(dmask, cv2.COLOR_RGB2GRAY)
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
            color=self.settings.line_color,
            width=self.settings.line_width,
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
        bg_rgb: tuple[int, int, int] | None = None,
        bg_del_margin: int = 0,
        extend_margin: int = 0,
    ) -> np.ndarray:
        for cnt in cnts:
            if cv2.contourArea(cnt) < min_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            if bg_rgb is not None:
                x1, x2 = x, x + w
                y1, y2 = y, y + h
                if w > 2 * bg_del_margin:
                    x1, x2 = x1 + bg_del_margin, x2 - bg_del_margin
                if h > 2 * bg_del_margin:
                    y1, y2 = y1 + bg_del_margin, y2 - bg_del_margin
                if np.all(src[y1:y2, x1:x2] == list(bg_rgb)):
                    continue

            cv2.rectangle(
                dst,
                (x - extend_margin, y - extend_margin),
                (x + w + extend_margin, y + h + extend_margin),
                color,
                width,
            )
        return dst
