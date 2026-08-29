"""Bitmap Font Atlas Generator for Persian.

Generates a bitmap font atlas from a TTF font (Vazirmatn) for injection
into the MAGES. engine. The atlas is a PNG/DDS texture containing all
needed Persian glyphs laid out in a grid, with a metadata file mapping
character codes to atlas coordinates.

This replaces the engine's default Japanese bitmap font (which has no
Persian/Arabic glyphs) with one that can render shaped Persian text.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


# Persian character set to include in the atlas
# Includes: Persian letters, Arabic presentation forms, digits, punctuation, ZWNJ
PERSIAN_BASE_CHARS = list("آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")

# Arabic presentation forms (what arabic_reshaper outputs)
# These are the shaped/connected forms that the game actually renders
PERSIAN_PRESENTATION_FORMS = [
    # Arabic letters (base + presentation forms A/B)
    chr(c) for c in range(0xFB50, 0xFEFF)
    if chr(c).isprintable()
]

# Persian-specific characters
PERSIAN_EXTRA = list("۰۱۲۳۴۵۶۷۸۹۹ٴ،؛؟«»—ـ\u200c\u200e\u200f")

# Common Latin characters (for mixed text like D-Mail, SERN, IBN 5100)
LATIN_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -_.+*/()=!@#$%^&")

# Punctuation
PUNCTUATION = list(".,:;!?\"'`~@#$%^&*()-_=+[]{}|\\<>/")


@dataclass
class GlyphInfo:
    """Metadata for a single glyph in the atlas."""
    char: str
    char_code: int
    x: int  # Atlas X position (pixels)
    y: int  # Atlas Y position (pixels)
    width: int  # Glyph width (pixels)
    height: int  # Glyph height (pixels)
    advance: int  # Horizontal advance to next glyph
    bearing_x: int = 0
    bearing_y: int = 0


@dataclass
class AtlasConfig:
    """Configuration for atlas generation."""
    glyph_size: int = 32  # Base glyph cell size
    glyph_padding: int = 2  # Padding between glyphs
    atlas_size: int = 1024  # Atlas texture size (square)
    font_path: str = "assets/Vazirmatn-Regular.ttf"
    output_dir: str = "assets_fa/font/"
    font_name: str = "vazirmatn_fa"


def get_glyph_set() -> List[str]:
    """Get the complete set of characters to include in the atlas."""
    chars = set()
    
    # Persian base letters
    chars.update(PERSIAN_BASE_CHARS)
    
    # Persian extra (digits, punctuation, ZWNJ)
    chars.update(PERSIAN_EXTRA)
    
    # Arabic presentation forms (shaped letters)
    chars.update(PERSIAN_PRESENTATION_FORMS)
    
    # Latin (for mixed text)
    chars.update(LATIN_CHARS)
    
    # Punctuation
    chars.update(PUNCTUATION)
    
    # Sort for consistent layout
    return sorted(chars, key=lambda c: ord(c))


def compute_atlas_layout(
    chars: List[str],
    config: AtlasConfig,
) -> Dict[str, GlyphInfo]:
    """Compute the grid layout for glyphs in the atlas.
    
    Args:
        chars: List of characters to place
        config: Atlas configuration
    
    Returns:
        Dict mapping character to GlyphInfo
    """
    cell_size = config.glyph_size + config.glyph_padding * 2
    cols = config.atlas_size // cell_size
    rows = config.atlas_size // cell_size
    
    glyphs = {}
    for i, char in enumerate(chars):
        col = i % cols
        row = i // cols
        
        if row >= rows:
            raise ValueError(
                f"Atlas too small: {len(chars)} chars need {len(chars) // cols + 1} rows, "
                f"but atlas only has {rows} rows. Increase atlas_size."
            )
        
        x = col * cell_size + config.glyph_padding
        y = row * cell_size + config.glyph_padding
        
        glyphs[char] = GlyphInfo(
            char=char,
            char_code=ord(char),
            x=x,
            y=y,
            width=config.glyph_size,
            height=config.glyph_size,
            advance=config.glyph_size,
        )
    
    return glyphs


def generate_atlas_metadata(
    config: AtlasConfig,
    glyphs: Dict[str, GlyphInfo],
) -> Dict:
    """Generate the metadata JSON that maps characters to atlas positions.
    
    This file is read by the engine's font renderer (or our injection patch)
    to locate glyphs in the atlas texture.
    """
    return {
        "font_name": config.font_name,
        "atlas_size": config.atlas_size,
        "glyph_size": config.glyph_size,
        "glyph_padding": config.glyph_padding,
        "glyph_count": len(glyphs),
        "glyphs": [
            {
                "char": g.char,
                "code": g.char_code,
                "x": g.x,
                "y": g.y,
                "width": g.width,
                "height": g.height,
                "advance": g.advance,
                "bearing_x": g.bearing_x,
                "bearing_y": g.bearing_y,
            }
            for g in sorted(glyphs.values(), key=lambda g: g.char_code)
        ],
    }


def generate_atlas(config: AtlasConfig) -> Tuple[Dict, Dict[str, GlyphInfo]]:
    """Generate atlas metadata (actual PNG rendering requires FontForge or PIL).
    
    This function computes the layout and generates the metadata file.
    The actual texture rendering is done by fontforge_export.py or a PIL script.
    
    Args:
        config: Atlas configuration
    
    Returns:
        (metadata_dict, glyph_info_dict)
    """
    chars = get_glyph_set()
    print(f"Generating atlas for {len(chars)} glyphs...")
    
    glyphs = compute_atlas_layout(chars, config)
    metadata = generate_atlas_metadata(config, glyphs)
    
    # Save metadata
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    meta_path = output_dir / f"{config.font_name}_atlas.json"
    meta_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    
    print(f"Atlas layout: {len(chars)} glyphs in {config.atlas_size}x{config.atlas_size} texture")
    print(f"Metadata saved to: {meta_path}")
    print(f"\nNext step: Run fontforge_export.py to render the actual PNG atlas.")
    
    return metadata, glyphs


if __name__ == "__main__":
    config = AtlasConfig()
    generate_atlas(config)
