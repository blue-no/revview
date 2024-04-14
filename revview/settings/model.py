from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_FILE = "revview_settings.json"


def rgb_to_hex(code: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*code)


def hex_to_rgb(code: str) -> tuple[int, int, int]:
    return tuple(int(code[i : i + 2], 16) for i in range(0, 6, 2))


def change_brightness(code: tuple[int, int, int], ratio: float) -> None:
    return tuple(int(i * ratio) for i in code)


def get_default_settings() -> Settings:
    return Settings(
        line_color=(255, 0, 0),
        line_width=2,
        ignore_bg_rect=True,
        bg_color=(255, 255, 255),
    )


@dataclass
class Settings:

    line_color: tuple[int]
    line_width: int
    ignore_bg_rect: bool
    bg_color: tuple[int]

    @classmethod
    def initialize(cls: Settings) -> Settings:
        if Path(SETTINGS_FILE).is_file():
            return cls.read()
        inst = get_default_settings()
        inst.write()
        return inst

    @classmethod
    def read(cls: Settings) -> Settings:
        with Path(SETTINGS_FILE).open(mode="r") as f:
            d = json.load(fp=f)
        return cls(**d)

    def write(self) -> None:
        d = asdict(self)
        with Path(SETTINGS_FILE).open(mode="w") as f:
            json.dump(obj=d, fp=f, indent=2)
