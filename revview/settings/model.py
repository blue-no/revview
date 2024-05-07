# settings/model.py
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Settings:

    line_color: tuple[int] = (255, 85, 0)
    line_width: int = 2
    ignore_bg_rect: bool = True
    bg_color: tuple[int] = (255, 255, 255)
    apply_legacy: bool = False
    last_folder: str = "."
    enable_process_dpi_awareness: bool = True

    @classmethod
    def initialize(cls: Settings, fp: Path | str) -> Settings:
        if Path(fp).is_file():
            try:
                return cls.read(fp=fp)
            except:
                pass
        inst = cls()
        inst.write(fp=fp)
        return inst

    @classmethod
    def read(cls: Settings, fp: Path | str) -> Settings:
        with Path(fp).open(mode="r") as f:
            d = json.load(fp=f)
        return cls(**d)

    def write(self, fp: Path | str) -> None:
        d = asdict(self)
        with Path(fp).open(mode="w") as f:
            json.dump(obj=d, fp=f, indent=2)
