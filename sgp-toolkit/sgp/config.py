"""Project configuration and path management."""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectConfig:
    game_root: str = "D:/Games/STEINSGATE"
    backup_root: str = "D:/Games/STEINSGATE_BACKUP_CLEAN"
    work_root: str = "D:/Games/STEINSGATE_WORK"
    extracted_dir: str = "extracted"
    strings_dir: str = "extracted/strings"
    assets_fa_dir: str = "assets_fa"
    source_encoding: str = "shift_jis"
    target_encoding: str = "utf-8"
    target_language: str = "fa"
    font_size_dialog: int = 26
    font_size_default: int = 32
    font_name: str = "Vazirmatn"
    max_expansion_ratio: float = 1.5
    glossary_path: str = "docs/GLOSSARY.md"
    style_guide_path: str = "docs/STYLE_GUIDE.md"

    @classmethod
    def load(cls, path: str = "config/project.json") -> "ProjectConfig":
        p = Path(path)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: str = "config/project.json") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(self.__dict__, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


@dataclass
class FontConfig:
    source_font: str = "Vazirmatn"
    source_font_path: str = "assets/Vazirmatn-Regular.ttf"
    atlas_output_dir: str = "assets_fa/font/"
    glyph_size: int = 32
    glyph_padding: int = 2
    atlas_texture_size: int = 1024
    font_name_in_game: str = "vazirmatn_fa"
    replace_original: bool = False  # if False, add as new font slot

    @classmethod
    def load(cls, path: str = "config/font_config.json") -> "FontConfig":
        p = Path(path)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self, path: str = "config/font_config.json") -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(self.__dict__, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
