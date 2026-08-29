"""Command-line interface for sgp-toolkit.

Usage:
    sgp export --input <scx_file_or_dir> --output <json_dir>
    sgp import --input <json_dir> --output <scx_dir> [--original <original_scx_dir>]
    sgp validate --input <json_dir> [--glossary <glossary.json>]
    sgp roundtrip --input <scx_file>
    sgp extract-mpk --input <mpk_file> --output <dir>
    sgp pack-mpk --input <dir> --output <mpk_file>
    sgp shape --text "سلام" [--no-latin-wrap]
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict

from .config import ProjectConfig
from .scx_parser import (
    parse_scx, write_scx, export_to_json, import_from_json, roundtrip_test
)
from .mpk_extractor import parse_mpk, extract_all, pack_mpk
from .encoding import convert_encoding, detect_encoding, normalize_string
from .shaping import process_persian, should_process
from .validator import validate_all_keywords, generate_report as val_report
from .glossary import check_all, generate_report as gl_report, load_glossary


def cmd_export(args):
    """Export SCX files to JSON."""
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob("*.scx"))
    
    total_strings = 0
    for scx_file in files:
        data = scx_file.read_bytes()
        scx = parse_scx(data, scx_file.name)
        json_data = export_to_json(scx)
        
        out_file = output_path / (scx_file.stem + ".json")
        out_file.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        total_strings += len(scx.strings)
        print(f"  {scx_file.name}: {len(scx.strings)} strings → {out_file.name}")
    
    # Write summary
    summary = {
        "total_files": len(files),
        "total_strings": total_strings,
        "files": [f.name for f in files],
    }
    (output_path / "_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nExported {total_strings} strings from {len(files)} files.")


def cmd_import(args):
    """Import JSON translations back to SCX."""
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    original_dir = Path(args.original) if args.original else None
    
    json_files = list(input_path.glob("*.json"))
    json_files = [f for f in json_files if not f.name.startswith("_")]
    
    for json_file in json_files:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        
        # Load original binary if available
        original_raw = None
        if original_dir:
            orig_path = original_dir / data.get("file", json_file.stem + ".scx")
            if orig_path.exists():
                original_raw = orig_path.read_bytes()
        
        scx = import_from_json(data, original_raw=original_raw)
        output = write_scx(scx)
        
        out_file = output_path / data.get("file", json_file.stem + ".scx")
        out_file.write_bytes(output)
        translated = sum(1 for s in scx.strings if s.fa)
        print(f"  {json_file.name}: {translated}/{len(scx.strings)} translated → {out_file.name}")
    
    print(f"\nImported {len(json_files)} files.")


def cmd_validate(args):
    """Validate translations for glossary consistency and keyword safety."""
    input_path = Path(args.input)
    
    # Collect all translations
    translations = {}
    for json_file in input_path.glob("*.json"):
        if json_file.name.startswith("_"):
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        for s in data.get("strings", []):
            if s.get("fa"):
                translations[s["id"]] = s["fa"]
    
    if not translations:
        print("No translations found to validate.")
        return
    
    # Glossary check
    glossary = load_glossary(args.glossary) if args.glossary else None
    violations = check_all(translations, glossary)
    print(gl_report(violations))
    
    # Keyword validation
    from .validator import TRIGGER_TABLE, load_trigger_table
    if not TRIGGER_TABLE:
        trigger_path = Path("config/trigger_keywords.json")
        if trigger_path.exists():
            load_trigger_table(str(trigger_path))
    
    if TRIGGER_TABLE:
        print()
        results = validate_all_keywords(translations)
        print(val_report(results))
    else:
        print("\n(No trigger keyword table loaded — skipping keyword validation)")


def cmd_roundtrip(args):
    """Test roundtrip integrity of an SCX file."""
    data = Path(args.input).read_bytes()
    success, message = roundtrip_test(data, Path(args.input).name)
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        sys.exit(1)


def cmd_extract_mpk(args):
    """Extract files from an MPK archive."""
    data = Path(args.input).read_bytes()
    archive = parse_mpk(data)
    output_dir = Path(args.output)
    results = extract_all(archive, output_dir)
    
    success = sum(1 for _, ok in results if ok)
    failed = sum(1 for _, ok in results if not ok)
    print(f"Extracted {success} files ({failed} failed) to {output_dir}")
    
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")


def cmd_pack_mpk(args):
    """Pack files into an MPK archive."""
    input_dir = Path(args.input)
    files = {}
    for f in input_dir.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(input_dir))
            files[rel] = f.read_bytes()
    
    output = pack_mpk(files)
    Path(args.output).write_bytes(output)
    print(f"Packed {len(files)} files into {args.output} ({len(output)} bytes)")


def cmd_shape(args):
    """Process Persian text through the shaping pipeline."""
    from .shaping import process_persian, is_persian
    
    text = args.text
    if not is_persian(text):
        print(f"(No Persian characters detected — output unchanged)")
        print(text)
        return
    
    result = process_persian(text, wrap_latin=not args.no_latin_wrap)
    print(f"Input:  {text}")
    print(f"Output: {result}")
    print(f"Bytes:  {result.encode('utf-8').hex()}")


def main():
    parser = argparse.ArgumentParser(
        prog="sgp",
        description="Steins;Gate Persian Localization Toolkit",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    
    # Export
    p = sub.add_parser("export", help="Export SCX files to JSON")
    p.add_argument("--input", "-i", required=True, help="SCX file or directory")
    p.add_argument("--output", "-o", required=True, help="Output JSON directory")
    p.set_defaults(func=cmd_export)
    
    # Import
    p = sub.add_parser("import", help="Import JSON translations to SCX")
    p.add_argument("--input", "-i", required=True, help="JSON directory")
    p.add_argument("--output", "-o", required=True, help="Output SCX directory")
    p.add_argument("--original", help="Original SCX directory for bytecode preservation")
    p.set_defaults(func=cmd_import)
    
    # Validate
    p = sub.add_parser("validate", help="Validate translations")
    p.add_argument("--input", "-i", required=True, help="JSON directory with translations")
    p.add_argument("--glossary", help="Custom glossary JSON path")
    p.set_defaults(func=cmd_validate)
    
    # Roundtrip
    p = sub.add_parser("roundtrip", help="Test SCX roundtrip integrity")
    p.add_argument("--input", "-i", required=True, help="SCX file to test")
    p.set_defaults(func=cmd_roundtrip)
    
    # Extract MPK
    p = sub.add_parser("extract-mpk", help="Extract MPK archive")
    p.add_argument("--input", "-i", required=True, help="MPK file")
    p.add_argument("--output", "-o", required=True, help="Output directory")
    p.set_defaults(func=cmd_extract_mpk)
    
    # Pack MPK
    p = sub.add_parser("pack-mpk", help="Pack files into MPK archive")
    p.add_argument("--input", "-i", required=True, help="Input directory")
    p.add_argument("--output", "-o", required=True, help="Output MPK file")
    p.set_defaults(func=cmd_pack_mpk)
    
    # Shape
    p = sub.add_parser("shape", help="Process Persian text (shaping + BiDi)")
    p.add_argument("--text", "-t", required=True, help="Text to process")
    p.add_argument("--no-latin-wrap", action="store_true", help="Skip Latin segment wrapping")
    p.set_defaults(func=cmd_shape)
    
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
