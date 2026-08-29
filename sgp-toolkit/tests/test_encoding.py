"""Tests for encoding utilities."""

import pytest
from sgp.encoding import (
    strip_bom, read_shift_jis, read_utf8, write_utf8_no_bom,
    detect_encoding, convert_encoding, normalize_string, UTF8_BOM,
)


def test_strip_bom():
    """Test BOM removal."""
    assert strip_bom(b"\xef\xbb\xbfhello") == b"hello"
    assert strip_bom(b"hello") == b"hello"
    assert strip_bom(b"") == b""


def test_read_shift_jis():
    """Test Shift-JIS decoding."""
    # "こんにちは" in Shift-JIS
    data = "こんにちは".encode("shift_jis")
    assert read_shift_jis(data) == "こんにちは"


def test_read_utf8():
    """Test UTF-8 reading with BOM stripping."""
    text = "سلام"
    # With BOM
    data = UTF8_BOM + text.encode("utf-8")
    assert read_utf8(data) == text
    # Without BOM
    data = text.encode("utf-8")
    assert read_utf8(data) == text


def test_write_utf8_no_bom():
    """Test that UTF-8 output never has BOM."""
    text = "سلام"
    result = write_utf8_no_bom(text)
    assert not result.startswith(UTF8_BOM)
    assert result.decode("utf-8") == text


def test_detect_encoding():
    """Test encoding detection."""
    # UTF-8 with BOM
    assert detect_encoding(UTF8_BOM + b"hello") == "utf-8"
    # Plain UTF-8 (Persian)
    assert detect_encoding("سلام".encode("utf-8")) == "utf-8"
    # Shift-JIS (Japanese)
    assert detect_encoding("こんにちは".encode("shift_jis")) == "shift_jis"


def test_convert_encoding():
    """Test encoding conversion."""
    jp_text = "こんにちは"
    sjis_data = jp_text.encode("shift_jis")
    utf8_data = convert_encoding(sjis_data, "shift_jis", "utf-8")
    assert not utf8_data.startswith(UTF8_BOM)
    assert utf8_data.decode("utf-8") == jp_text


def test_normalize_string():
    """Test string normalization."""
    # BOM character removal
    assert normalize_string("\ufeffسلام") == "سلام"
    # Line ending normalization
    assert normalize_string("line1\r\nline2") == "line1\nline2"
    assert normalize_string("line1\rline2") == "line1\nline2"
    # Null removal
    assert normalize_string("text\x00more") == "textmore"
