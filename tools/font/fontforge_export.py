#!/usr/bin/env python3
"""FontForge batch export script for Persian bitmap font generation.

This script runs inside FontForge to:
1. Open the Vazirmatn TTF font
2. Export each needed glyph as a PNG at the specified size
3. Generate the atlas texture by compositing glyphs into a grid

Usage in FontForge:
    fontforge -script fontforge_export.py

Or from command line:
    fontforge -lang=py -script fontforge_export.py
"""

import sys
import os
import json
from pathlib import Path

# FontForge Python interface
try:
    import fontforge
    import psMat
except ImportError:
    print("This script must be run with FontForge's Python:")
    print("  fontforge -lang=py -script fontforge_export.py")
    sys.exit(1)


# Configuration
FONT_PATH = "assets/Vazirmatn-Regular.ttf"
OUTPUT_DIR = "assets_fa/font"
GLYPH_SIZE = 32
ATLAS_SIZE = 1024
FONT_NAME = "vazirmatn_fa"


def export_glyphs():
    """Export all needed Persian glyphs from the font."""
    font = fontforge.open(FONT_PATH)
    
    # Load the atlas metadata to know which glyphs we need
    meta_path = os.path.join(OUTPUT_DIR, f"{FONT_NAME}_atlas.json")
    if not os.path.exists(meta_path):
        print(f"Error: Atlas metadata not found at {meta_path}")
        print("Run atlas_generator.py first to compute the layout.")
        sys.exit(1)
    
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # Create temp directory for individual glyph PNGs
    temp_dir = os.path.join(OUTPUT_DIR, "temp_glyphs")
    os.makedirs(temp_dir, exist_ok=True)
    
    exported = 0
    missing = 0
    
    for glyph_info in metadata["glyphs"]:
        char_code = glyph_info["code"]
        char = chr(char_code)
        
        # Find the glyph in the font
        glyph_name = font.findEncodingSlot(char_code)
        if glyph_name is None or glyph_name < 0:
            # Try to create it
            try:
                font.selection.select(("unicode", None), char_code)
                font.charFromCode(char_code)
            except Exception:
                print(f"  Missing glyph: U+{char_code:04X} ({char})")
                missing += 1
                continue
        
        # Export as PNG
        glyph = font[char_code] if char_code in font else None
        if glyph is None:
            print(f"  Cannot access glyph: U+{char_code:04X}")
            missing += 1
            continue
        
        png_path = os.path.join(temp_dir, f"u{char_code:04x}.png")
        try:
            glyph.export(png_path, GLYPH_SIZE, GLYPH_SIZE)
            exported += 1
        except Exception as e:
            print(f"  Export failed: U+{char_code:04X}: {e}")
            missing += 1
    
    print(f"\nExported: {exported} glyphs")
    print(f"Missing:  {missing} glyphs")
    print(f"Temp PNGs in: {temp_dir}")
    print(f"\nNext: Composite individual PNGs into atlas texture.")
    
    font.close()


def composite_atlas():
    """Composite individual glyph PNGs into a single atlas texture.
    
    This would typically use PIL (Pillow) to create the final atlas.
    Run after export_glyphs().
    """
    try:
        from PIL import Image
    except ImportError:
        print("PIL (Pillow) is required for atlas compositing.")
        print("Install with: pip install Pillow")
        return
    
    meta_path = os.path.join(OUTPUT_DIR, f"{FONT_NAME}_atlas.json")
    temp_dir = os.path.join(OUTPUT_DIR, "temp_glyphs")
    atlas_path = os.path.join(OUTPUT_DIR, f"{FONT_NAME}_atlas.png")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    atlas = Image.new("RGBA", (ATLAS_SIZE, ATLAS_SIZE), (0, 0, 0, 0))
    
    placed = 0
    for glyph_info in metadata["glyphs"]:
        char_code = glyph_info["code"]
        png_path = os.path.join(temp_dir, f"u{char_code:04x}.png")
        
        if not os.path.exists(png_path):
            continue
        
        glyph_img = Image.open(png_path).convert("RGBA")
        atlas.paste(glyph_img, (glyph_info["x"], glyph_info["y"]))
        placed += 1
    
    atlas.save(atlas_path)
    print(f"Atlas saved: {atlas_path} ({placed} glyphs placed)")
    
    # Clean up temp
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("Temp glyphs cleaned up.")


if __name__ == "__main__":
    print("=== FontForge Persian Bitmap Font Generator ===")
    print()
    export_glyphs()
    print()
    composite_atlas()
    print()
    print("Done! Atlas PNG and metadata are ready for game injection.")
