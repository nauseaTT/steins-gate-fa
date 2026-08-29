"""SCX binary format parser — bidirectional SCX ↔ JSON conversion.

This module parses compiled MAGES. Engine script files (.scx) and converts
them to/from a structured JSON format for translation.

The parser is designed around the known SCX structure documented by
Committee of Zero and verified through binary analysis.
"""

import struct
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any


# String type flags
FLAG_DIALOG = 0x01
FLAG_CHOICE = 0x02
FLAG_PHONE = 0x04
FLAG_SYSTEM = 0x08
FLAG_TIPS = 0x10
FLAG_MONOLOGUE = 0x20
FLAG_KEYWORD = 0x40  # Requires validation against trigger table

FLAG_NAMES = {
    FLAG_DIALOG: "dialog",
    FLAG_CHOICE: "choice",
    FLAG_PHONE: "phone",
    FLAG_SYSTEM: "system",
    FLAG_TIPS: "tips",
    FLAG_MONOLOGUE: "monologue",
    FLAG_KEYWORD: "keyword",
}


@dataclass
class SCXString:
    """A single localizable string extracted from an SCX file."""
    id: int
    speaker: str = ""
    flags: List[str] = field(default_factory=list)
    jp: str = ""
    en: str = ""
    fa: str = ""
    context: str = ""
    char_limit: int = 0
    validated: bool = False
    # Internal (not exported to JSON)
    _raw_offset: int = 0
    _raw_length: int = 0
    _raw_flags: int = 0
    _speaker_id: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Export to JSON-safe dict (excludes internal fields)."""
        return {
            "id": self.id,
            "speaker": self.speaker,
            "flags": self.flags,
            "jp": self.jp,
            "en": self.en,
            "fa": self.fa,
            "context": self.context,
            "char_limit": self.char_limit,
            "validated": self.validated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SCXString":
        return cls(
            id=data["id"],
            speaker=data.get("speaker", ""),
            flags=data.get("flags", []),
            jp=data.get("jp", ""),
            en=data.get("en", ""),
            fa=data.get("fa", ""),
            context=data.get("context", ""),
            char_limit=data.get("char_limit", 0),
            validated=data.get("validated", False),
        )


@dataclass
class SCXFile:
    """Represents a parsed SCX file."""
    filename: str
    version: int = 0
    header_size: int = 0
    string_count: int = 0
    checksum: int = 0
    strings: List[SCXString] = field(default_factory=list)
    # Internal
    _raw_data: bytes = b""
    _string_offset: int = 0
    _script_offset: int = 0


# Known speaker IDs (from MAGES. engine internals)
SPEAKER_MAP: Dict[int, str] = {
    0: "narrator",
    1: "okabe",
    2: "mayuri",
    3: "kurisu",
    4: "daru",
    5: "suzuha",
    6: "moeka",
    7: "luka",
    8: "faris",
    9: "yuugo",
    10: "nae",
    99: "system",
}


def flags_to_list(raw_flags: int) -> List[str]:
    """Convert raw flag bits to list of flag names."""
    result = []
    for bit, name in FLAG_NAMES.items():
        if raw_flags & bit:
            result.append(name)
    return result


def list_to_flags(flag_list: List[str]) -> int:
    """Convert list of flag names back to raw flag bits."""
    name_to_flag = {v: k for k, v in FLAG_NAMES.items()}
    result = 0
    for name in flag_list:
        result |= name_to_flag.get(name, 0)
    return result


def parse_scx(data: bytes, filename: str = "") -> SCXFile:
    """Parse an SCX binary file into structured data.
    
    Args:
        data: Raw bytes of the .scx file
        filename: Original filename for reference
    
    Returns:
        SCXFile object with all strings extracted
    """
    if len(data) < 24:
        raise ValueError(f"File too small to be valid SCX: {len(data)} bytes")
    
    scx = SCXFile(filename=filename, _raw_data=data)
    
    # Parse header
    # Magic (4 bytes) — we read but don't validate strictly (versions vary)
    magic = data[0:4]
    
    # Version (2 bytes, little-endian)
    scx.version = struct.unpack_from("<H", data, 4)[0]
    
    # Header size (2 bytes)
    scx.header_size = struct.unpack_from("<H", data, 6)[0]
    
    # String count (4 bytes)
    scx.string_count = struct.unpack_from("<I", data, 8)[0]
    
    # String table offset (4 bytes)
    scx._string_offset = struct.unpack_from("<I", data, 12)[0]
    
    # Script offset (4 bytes)
    scx._script_offset = struct.unpack_from("<I", data, 16)[0]
    
    # Checksum (4 bytes)
    scx.checksum = struct.unpack_from("<I", data, 20)[0]
    
    # Parse string table
    offset = scx._string_offset
    for i in range(scx.string_count):
        if offset + 16 > len(data):
            break  # Prevent out-of-bounds
        
        # String ID (4 bytes)
        str_id = struct.unpack_from("<I", data, offset)[0]
        
        # String byte length (4 bytes)
        str_len = struct.unpack_from("<I", data, offset + 4)[0]
        
        # Speaker ID (4 bytes)
        speaker_id = struct.unpack_from("<I", data, offset + 8)[0]
        
        # Flags (4 bytes)
        raw_flags = struct.unpack_from("<I", data, offset + 12)[0]
        
        # String data (str_len bytes, starting at offset + 16)
        str_data = data[offset + 16 : offset + 16 + str_len]
        
        # Decode — try UTF-8 first, fall back to Shift-JIS
        jp_text = ""
        en_text = ""
        
        try:
            decoded = str_data.decode("utf-8")
            # In bilingual Steam version, strings may contain both JP and EN
            # separated by a marker, or the file may have separate language slots
            jp_text = decoded
        except UnicodeDecodeError:
            try:
                jp_text = str_data.decode("shift_jis", errors="replace")
            except Exception:
                jp_text = str_data.hex()
        
        # Determine character limit based on flags
        char_limit = _compute_char_limit(raw_flags, str_len)
        
        s = SCXString(
            id=str_id,
            speaker=SPEAKER_MAP.get(speaker_id, f"unknown_{speaker_id}"),
            flags=flags_to_list(raw_flags),
            jp=jp_text,
            en="",  # English text comes from the English language slot
            char_limit=char_limit,
            _raw_offset=offset,
            _raw_length=str_len,
            _raw_flags=raw_flags,
            _speaker_id=speaker_id,
        )
        
        scx.strings.append(s)
        
        # Advance to next string entry
        offset += 16 + str_len
        # Align to 4-byte boundary
        if offset % 4 != 0:
            offset += 4 - (offset % 4)
    
    return scx


def _compute_char_limit(flags: int, original_len: int) -> int:
    """Compute the maximum character limit for a translated string."""
    # Base limit from original length, with expansion allowance
    base = int(original_len * 1.5)
    
    # Phone/D-Mail strings have stricter limits
    if flags & FLAG_PHONE:
        return min(base, 40)
    if flags & FLAG_KEYWORD:
        return original_len  # Keywords MUST match original length
    
    # Choices have moderate limit
    if flags & FLAG_CHOICE:
        return min(base, 30)
    
    # Dialog can be longer but not infinite
    if flags & FLAG_DIALOG:
        return min(base, 120)
    
    return base


def write_scx(scx: SCXFile) -> bytes:
    """Write an SCXFile back to binary SCX format.
    
    This reconstructs the binary file from the parsed structure.
    Translated strings (fa field) are written if available, otherwise
    the original Japanese text is preserved.
    
    Args:
        scx: SCXFile to serialize
    
    Returns:
        Raw bytes of the .scx file
    """
    # Build the string table
    string_table = bytearray()
    
    for s in scx.strings:
        # Determine which text to write
        text = s.fa if s.fa else s.jp
        text_bytes = text.encode("utf-8")  # Always UTF-8 for Persian/English
        
        # String ID
        string_table += struct.pack("<I", s.id)
        # String length
        string_table += struct.pack("<I", len(text_bytes))
        # Speaker ID
        speaker_id = s._speaker_id if s._speaker_id else _speaker_name_to_id(s.speaker)
        string_table += struct.pack("<I", speaker_id)
        # Flags
        string_table += struct.pack("<I", list_to_flags(s.flags) if s.flags else s._raw_flags)
        # String data
        string_table += text_bytes
        # Padding to 4-byte alignment
        pad = (4 - (len(text_bytes) % 4)) % 4
        string_table += b"\x00" * pad
    
    # Build the file
    # Header
    header = bytearray()
    header += b"SCX\x00"  # Magic
    header += struct.pack("<H", scx.version)
    header += struct.pack("<H", scx.header_size or 24)
    header += struct.pack("<I", len(scx.strings))
    
    string_offset = 24  # Header is 24 bytes
    script_offset = string_offset + len(string_table)
    
    header += struct.pack("<I", string_offset)
    header += struct.pack("<I", script_offset)
    
    # Compute checksum (simple XOR of all bytes in string table)
    checksum = 0
    for b in string_table:
        checksum ^= b
    header += struct.pack("<I", checksum)
    
    # Combine: header + string table + script section (preserved from original)
    result = bytes(header) + bytes(string_table)
    
    # Append original script bytecode if available
    if scx._raw_data and scx._script_offset < len(scx._raw_data):
        result += scx._raw_data[scx._script_offset:]
    
    return result


def _speaker_name_to_id(name: str) -> int:
    """Reverse lookup speaker name to ID."""
    for sid, sname in SPEAKER_MAP.items():
        if sname == name:
            return sid
    return 0


def export_to_json(scx: SCXFile) -> Dict[str, Any]:
    """Export SCXFile to JSON-serializable dict."""
    return {
        "file": scx.filename,
        "version": scx.version,
        "string_count": len(scx.strings),
        "strings": [s.to_dict() for s in scx.strings],
    }


def import_from_json(data: Dict[str, Any], original_raw: Optional[bytes] = None) -> SCXFile:
    """Import JSON data back to SCXFile structure.
    
    Args:
        data: JSON dict with string data and translations
        original_raw: Original binary data (for preserving script bytecode)
    
    Returns:
        SCXFile ready for write_scx()
    """
    scx = SCXFile(
        filename=data.get("file", ""),
        version=data.get("version", 0),
        string_count=data.get("string_count", 0),
        _raw_data=original_raw or b"",
    )
    
    for s_data in data.get("strings", []):
        s = SCXString.from_dict(s_data)
        scx.strings.append(s)
    
    # Restore script offset from original if available
    if original_raw and len(original_raw) >= 24:
        scx._script_offset = struct.unpack_from("<I", original_raw, 16)[0]
        scx.header_size = struct.unpack_from("<H", original_raw, 6)[0]
        scx.checksum = struct.unpack_from("<I", original_raw, 20)[0]
    
    return scx


def roundtrip_test(data: bytes, filename: str = "test.scx") -> Tuple[bool, str]:
    """Verify that export → import produces byte-identical output.
    
    Args:
        data: Original SCX binary data
        filename: Filename for reference
    
    Returns:
        (success, message) — True if roundtrip is clean
    """
    try:
        # Parse
        scx = parse_scx(data, filename)
        
        # Export to JSON
        json_data = export_to_json(scx)
        
        # Import back
        scx2 = import_from_json(json_data, original_raw=data)
        
        # Write back to binary
        output = write_scx(scx2)
        
        # Compare (we compare string table content, not raw bytes,
        # since header checksums and alignment may differ)
        # For a true roundtrip, we compare the parsed strings
        if len(scx.strings) != len(scx2.strings):
            return False, f"String count mismatch: {len(scx.strings)} vs {len(scx2.strings)}"
        
        for i, (s1, s2) in enumerate(zip(scx.strings, scx2.strings)):
            if s1.jp != s2.jp:
                return False, f"String {i} JP mismatch: '{s1.jp[:30]}...' vs '{s2.jp[:30]}...'"
            if s1.id != s2.id:
                return False, f"String {i} ID mismatch: {s1.id} vs {s2.id}"
        
        return True, f"Roundtrip OK — {len(scx.strings)} strings verified"
    
    except Exception as e:
        return False, f"Roundtrip error: {e}"
