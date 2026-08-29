"""Tests for SCX parser roundtrip and string extraction."""

import pytest
import struct
from sgp.scx_parser import (
    parse_scx, write_scx, export_to_json, import_from_json,
    roundtrip_test, SCXString, SCXFile, flags_to_list, list_to_flags,
    FLAG_DIALOG, FLAG_PHONE, FLAG_KEYWORD,
)


def make_test_scx():
    """Create a minimal valid SCX binary for testing."""
    # Header
    header = bytearray()
    header += b"SCX\x00"
    header += struct.pack("<H", 2)  # version
    header += struct.pack("<H", 24)  # header size
    header += struct.pack("<I", 2)  # string count
    
    # String table will start right after header
    string_offset = 24
    header += struct.pack("<I", string_offset)
    
    # Script section offset (after strings)
    # We'll calculate this after building strings
    # For now, placeholder
    header += struct.pack("<I", 0)  # script offset (no script for test)
    header += struct.pack("<I", 0)  # checksum
    
    # String table
    str_table = bytearray()
    
    # String 0: "こんにちは" (dialog)
    text0 = "こんにちは".encode("utf-8")
    str_table += struct.pack("<I", 0)  # id
    str_table += struct.pack("<I", len(text0))  # length
    str_table += struct.pack("<I", 1)  # speaker (okabe)
    str_table += struct.pack("<I", FLAG_DIALOG)  # flags
    str_table += text0
    # Pad to 4 bytes
    pad = (4 - (len(text0) % 4)) % 4
    str_table += b"\x00" * pad
    
    # String 1: "キーワード" (phone keyword)
    text1 = "キーワード".encode("utf-8")
    str_table += struct.pack("<I", 1)  # id
    str_table += struct.pack("<I", len(text1))  # length
    str_table += struct.pack("<I", 0)  # speaker (narrator)
    str_table += struct.pack("<I", FLAG_PHONE | FLAG_KEYWORD)  # flags
    str_table += text1
    pad = (4 - (len(text1) % 4)) % 4
    str_table += b"\x00" * pad
    
    # Update script offset
    script_offset = string_offset + len(str_table)
    struct.pack_into("<I", header, 16, script_offset)
    
    return bytes(header) + bytes(str_table)


def test_parse_scx():
    """Test that SCX parsing extracts correct strings."""
    data = make_test_scx()
    scx = parse_scx(data, "test.scx")
    
    assert scx.filename == "test.scx"
    assert scx.version == 2
    assert scx.string_count == 2
    assert len(scx.strings) == 2
    
    # First string
    assert scx.strings[0].id == 0
    assert scx.strings[0].speaker == "okabe"
    assert "dialog" in scx.strings[0].flags
    assert scx.strings[0].jp == "こんにちは"
    
    # Second string
    assert scx.strings[1].id == 1
    assert "phone" in scx.strings[1].flags
    assert "keyword" in scx.strings[1].flags


def test_flags_conversion():
    """Test flag bit <-> name conversion."""
    raw = FLAG_DIALOG | FLAG_PHONE
    names = flags_to_list(raw)
    assert "dialog" in names
    assert "phone" in names
    
    raw2 = list_to_flags(["dialog", "phone"])
    assert raw2 == raw


def test_export_import_json():
    """Test JSON export/import preserves string data."""
    data = make_test_scx()
    scx = parse_scx(data, "test.scx")
    
    # Export
    json_data = export_to_json(scx)
    assert json_data["file"] == "test.scx"
    assert json_data["string_count"] == 2
    
    # Import
    scx2 = import_from_json(json_data, original_raw=data)
    assert len(scx2.strings) == 2
    assert scx2.strings[0].jp == scx.strings[0].jp
    assert scx2.strings[1].jp == scx.strings[1].jp


def test_roundtrip():
    """Test that roundtrip produces consistent results."""
    data = make_test_scx()
    success, message = roundtrip_test(data, "test.scx")
    assert success, message


def test_translation_write():
    """Test that translated text is written correctly."""
    data = make_test_scx()
    scx = parse_scx(data, "test.scx")
    
    # Add Persian translation
    scx.strings[0].fa = "سلام"
    scx.strings[1].fa = "کلمه کلیدی"
    
    # Write back
    output = write_scx(scx)
    
    # Parse again
    scx2 = parse_scx(output, "output.scx")
    assert scx2.strings[0].jp == "سلام"  # fa text goes into the jp slot (same string field)
    assert scx2.strings[1].jp == "کلمه کلیدی"


def test_char_limit():
    """Test character limit computation for different flag types."""
    data = make_test_scx()
    scx = parse_scx(data, "test.scx")
    
    # Dialog string should have a generous limit
    assert scx.strings[0].char_limit > 0
    
    # Keyword string should have a strict limit (matching original length)
    assert scx.strings[1].char_limit > 0
    # Keyword char_limit should be <= original byte length (strict)
