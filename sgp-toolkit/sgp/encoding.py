"""Encoding utilities: Shift-JIS ↔ UTF-8 conversion with BOM safety."""

import codecs
from pathlib import Path
from typing import Tuple, Optional


# BOM bytes for detection and removal
UTF8_BOM = b"\xef\xbb\xbf"


def strip_bom(data: bytes) -> bytes:
    """Remove UTF-8 BOM if present."""
    if data.startswith(UTF8_BOM):
        return data[3:]
    return data


def read_shift_jis(data: bytes, errors: str = "replace") -> str:
    """Decode bytes as Shift-JIS (cp932), handling encoding issues gracefully."""
    return data.decode("shift_jis", errors=errors)


def read_utf8(data: bytes, errors: str = "replace") -> str:
    """Decode bytes as UTF-8, stripping BOM first."""
    return strip_bom(data).decode("utf-8", errors=errors)


def write_utf8_no_bom(text: str) -> bytes:
    """Encode text as UTF-8 without BOM — CRITICAL for MAGES. engine compatibility."""
    return text.encode("utf-8")


def detect_encoding(data: bytes) -> str:
    """Attempt to detect the encoding of binary text data.
    
    Returns 'shift_jis', 'utf-8', or 'unknown'.
    """
    # Check for BOM
    if data.startswith(UTF8_BOM):
        return "utf-8"
    
    # Try UTF-8 first (strict)
    try:
        data.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    
    # Try Shift-JIS
    try:
        data.decode("shift_jis")
        return "shift_jis"
    except UnicodeDecodeError:
        pass
    
    return "unknown"


def convert_encoding(
    data: bytes,
    from_encoding: str = "shift_jis",
    to_encoding: str = "utf-8",
    errors: str = "replace",
) -> bytes:
    """Convert text data between encodings, ensuring no BOM in output."""
    # Decode source
    if from_encoding == "utf-8":
        text = read_utf8(data, errors)
    else:
        text = data.decode(from_encoding, errors=errors)
    
    # Encode target
    if to_encoding == "utf-8":
        return write_utf8_no_bom(text)
    else:
        return text.encode(to_encoding, errors=errors)


def normalize_string(text: str) -> str:
    """Normalize a text string for consistent processing.
    
    - Strips BOM character if present
    - Normalizes line endings to \\n
    - Removes null characters
    """
    # Remove BOM character
    if text and text[0] == "\ufeff":
        text = text[1:]
    
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove null characters
    text = text.replace("\x00", "")
    
    return text
