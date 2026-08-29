#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract.py — Steins;Gate Persian localization: Phase 2/10 extraction pipeline.

Wires the MagesTool (tools/mgstool.py, a port of CommitteeOfZero's
`ungelify`/`SciAdvNet.MagesVfs` MPK reader) to the project's required output
layout:

    GAME_ROOT
      ├── script.mpk   ──►  extracted/scripts_raw/   (all SCX/SCR files)
      └── system.mpk   ──►  extracted/system_texts/  (menus, TIPs, ...)
                                └── (font files also copied) ──► extracted/system_fonts/

Outputs:
    manifest.json              full file list + sizes + total SCX count

Usage:
    python3 tools/extract.py --game-root /path/to/STEINSGATE
    python3 tools/extract.py (auto-detects: --game-root, $GAME_ROOT, ./game)

It must run inside the project directory (it writes ./extracted and ./manifest.json).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
from pathlib import Path

# Make the script importable regardless of CWD by locating mgstool next to it.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mgstool import MpkArchive, MpkError  # noqa: E402

SCRIPT_ARCHIVES = ["script.mpk", "script_archive.mpk"]
SYSTEM_ARCHIVES = ["system.mpk"]

# --- font-file classification -------------------------------------------------
FONT_EXTENSIONS = {
    ".fnt", ".ttf", ".otf", ".ttc", ".f00", ".ftx", ".tbl",
    ".bft", ".sfc", ".pfm", ".pfb", ".fntx", ".otx",
}


def looks_like_font(name: str) -> bool:
    n = name.lower()
    if "font" in n:
        return True
    ext = Path(n).suffix.lower()
    return ext in FONT_EXTENSIONS


# --- archive discovery --------------------------------------------------------
def find_archive(root: Path, names):
    candidates = [root]
    # Steam ships the archives under USRDIR/.
    for depth in range(3):
        candidates += [p for p in root.rglob("USRDIR") if len(p.relative_to(root).parts) <= depth + 1]
    seen = set()
    for base in candidates:
        if base in seen:
            continue
        seen.add(base)
        for name in names:
            p = base / name
            if p.is_file():
                return p
    return None


def extract_archive(mpk_path: Path, out_dir: Path, extra_font_dir: Path | None):
    """Extract an MPK into out_dir; optionally mirror font files elsewhere."""
    try:
        arch = MpkArchive(str(mpk_path))
    except MpkError as e:
        return {"found": False, "error": str(e), "path": str(mpk_path)}

    out_dir.mkdir(parents=True, exist_ok=True)
    written = arch.extract_all(str(out_dir))

    files = []
    fonts = []
    for rel in written:
        p = out_dir / rel
        size = p.stat().st_size if p.exists() else 0
        files.append({"name": rel, "size_bytes": size})
        if extra_font_dir is not None and looks_like_font(rel):
            # Copy (non-destructive) so the font asset remains in both places.
            extra_font_dir.mkdir(parents=True, exist_ok=True)
            out_p = extra_font_dir / Path(rel).name
            out_p.write_bytes(p.read_bytes())
            fonts.append({"name": out_p.name, "size_bytes": out_p.stat().st_size,
                          "from": f"system.mpk:{rel}"})

    return {
        "found": True,
        "path": str(mpk_path),
        "version": f"v{arch.version_major}.{arch.version_minor}",
        "compressed": arch.is_compressed,
        "entry_count": len(arch.entries),
        "extracted_file_count": len(files),
        "files": files,
        "font_files": fonts,
    }


def build_manifest(out_root: Path, script_info, system_info, tool_info, game_root):
    def dir_files(d: Path):
        if not d.is_dir():
            return []
        out = []
        for f in sorted(d.iterdir()):
            if f.is_file():
                out.append({"name": f.name, "size_bytes": f.stat().st_size})
        return out

    scripts_raw = out_root / "scripts_raw"
    system_texts = out_root / "system_texts"
    system_fonts = out_root / "system_fonts"

    script_files = script_info.get("files", []) if script_info else []
    scx_count = sum(
        1 for f in script_files if Path(f["name"]).suffix.lower() in {".scx", ".scr"}
    )

    manifest = {
        "project": "Steins;Gate Persian Localization",
        "phase": "02/10 — Extract text files from game archives",
        "tool": tool_info,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "game_root": str(game_root),
        "source_archives": {
            "script.mpk": script_info,
            "system.mpk": system_info,
        },
        "outputs": {
            "scripts_raw": {
                "directory": str(scripts_raw),
                "file_count": len(script_files),
                "scx_file_count": scx_count,
                "files": script_files,
            },
            "system_texts": {
                "directory": str(system_texts),
                "file_count": len(system_info.get("files", [])) if system_info else 0,
                "files": system_info.get("files", []) if system_info else [],
            },
            "system_fonts": {
                "directory": str(system_fonts),
                "file_count": system_info["font_files"].__len__() if system_info else 0,
                "files": system_info.get("font_files", []) if system_info else [],
            },
        },
        "total_scx_files": scx_count,
    }
    return manifest


def main(argv):
    ap = argparse.ArgumentParser(description="S;G Phase 2 extraction pipeline")
    ap.add_argument("--game-root", default=None, help="path to the game folder")
    args = ap.parse_args(argv)

    project_root = Path.cwd()
    out_root = project_root / "extracted"

    game_root = args.game_root or os.environ.get("GAME_ROOT") or "game"
    game_root = Path(game_root)
    if not game_root.is_dir():
        game_root = project_root / game_root

    script_path = find_archive(game_root, SCRIPT_ARCHIVES) if game_root.is_dir() else None
    system_path = find_archive(game_root, SYSTEM_ARCHIVES) if game_root.is_dir() else None

    tool_info = {
        "name": "MagesTool",
        "origin": "CommitteeOfZero / SciAdv.Net (ungelify + SciAdvNet.MagesVfs)",
        "upstream": "https://github.com/CommitteeOfZero/SciAdv.Net",
        "implementation": "tools/mgstool.py",
    }

    script_info = None
    system_info = None

    if script_path:
        script_info = extract_archive(
            script_path, out_root / "scripts_raw", extra_font_dir=None
        )
    if system_path:
        system_info = extract_archive(
            system_path, out_root / "system_texts", extra_font_dir=out_root / "system_fonts"
        )

    # Ensure directories exist even when archives are missing (so the layout is
    # always there and git-trackable via .gitkeep).
    for d in ("scripts_raw", "system_texts", "system_fonts"):
        (out_root / d).mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(out_root, script_info, system_info, tool_info, game_root)

    with open(project_root / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    scx = manifest["total_scx_files"]
    print(f"manifest.json written")
    print(f"  script.mpk found : {bool(script_path)}")
    print(f"  system.mpk found : {bool(system_path)}")
    print(f"  total SCX files  : {scx}")
    if not script_path:
        print("NOTE: script.mpk not found under", game_root)
    if not system_path:
        print("NOTE: system.mpk not found under", game_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
