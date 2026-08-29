"""MPK archive extractor and packer for MAGES. Engine.

MPK (MAGES. Package) is the archive format used by MAGES. Engine games.
It contains multiple files (SCX scripts, images, sounds, etc.) with
optional LZSS/Deflate compression.

Structure:
  Header: magic "MPK\0" + version + file count + offset to file table
  File table: array of (filename_hash, offset, size, compressed_size, flags)
  Data section: concatenated file data (optionally compressed)
"""

import struct
import zlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


MPK_MAGIC = b"MPK\x00"
COMPRESSION_NONE = 0
COMPRESSION_LZSS = 1
COMPRESSION_DEFLATE = 2


@dataclass
class MPKEntry:
    """A single file entry within an MPK archive."""
    filename: str
    offset: int = 0
    size: int = 0  # Uncompressed size
    compressed_size: int = 0  # Compressed size (0 if uncompressed)
    compression: int = COMPRESSION_NONE
    hash: int = 0


@dataclass
class MPKArchive:
    """Represents a parsed MPK archive."""
    version: int = 0
    file_count: int = 0
    entries: List[MPKEntry] = field(default_factory=list)
    _raw_data: bytes = b""


def parse_mpk(data: bytes) -> MPKArchive:
    """Parse an MPK archive's file table.
    
    Args:
        data: Raw bytes of the .mpk file
    
    Returns:
        MPKArchive with file entries (data extracted separately)
    """
    if len(data) < 16:
        raise ValueError(f"File too small to be valid MPK: {len(data)} bytes")
    
    magic = data[0:4]
    if magic != MPK_MAGIC:
        # Some versions use different magic; try to continue anyway
        pass
    
    archive = MPKArchive(_raw_data=data)
    
    # Version (2 bytes)
    archive.version = struct.unpack_from("<H", data, 4)[0]
    
    # File count (4 bytes)
    archive.file_count = struct.unpack_from("<I", data, 8)[0]
    
    # File table offset (4 bytes)
    table_offset = struct.unpack_from("<I", data, 12)[0]
    
    # Parse file table
    # Each entry: hash(4) + offset(4) + size(4) + compressed_size(4) + flags(2) + name_len(2) + name(N)
    offset = table_offset
    for i in range(archive.file_count):
        if offset + 20 > len(data):
            break
        
        file_hash = struct.unpack_from("<I", data, offset)[0]
        file_offset = struct.unpack_from("<I", data, offset + 4)[0]
        file_size = struct.unpack_from("<I", data, offset + 8)[0]
        comp_size = struct.unpack_from("<I", data, offset + 12)[0]
        flags = struct.unpack_from("<H", data, offset + 16)[0]
        name_len = struct.unpack_from("<H", data, offset + 18)[0]
        
        # Read filename
        if offset + 20 + name_len > len(data):
            break
        filename = data[offset + 20 : offset + 20 + name_len].decode("utf-8", errors="replace")
        
        # Determine compression type
        compression = COMPRESSION_NONE
        if comp_size > 0 and comp_size != file_size:
            compression = COMPRESSION_DEFLATE  # Most common in Steam version
        
        entry = MPKEntry(
            filename=filename,
            offset=file_offset,
            size=file_size,
            compressed_size=comp_size,
            compression=compression,
            hash=file_hash,
        )
        archive.entries.append(entry)
        
        offset += 20 + name_len
        # Align to 4 bytes
        if offset % 4 != 0:
            offset += 4 - (offset % 4)
    
    return archive


def extract_file(archive: MPKArchive, entry: MPKEntry) -> bytes:
    """Extract a single file from an MPK archive.
    
    Args:
        archive: Parsed MPK archive
        entry: File entry to extract
    
    Returns:
        Uncompressed file bytes
    """
    data = archive._raw_data
    
    # Determine read size
    read_size = entry.compressed_size if entry.compressed_size > 0 else entry.size
    raw = data[entry.offset : entry.offset + read_size]
    
    # Decompress if needed
    if entry.compression == COMPRESSION_DEFLATE:
        try:
            return zlib.decompress(raw)
        except zlib.error:
            # Try raw deflate (no header)
            try:
                return zlib.decompress(raw, -15)
            except zlib.error:
                return raw  # Return as-is if decompression fails
    elif entry.compression == COMPRESSION_LZSS:
        # LZSS decompression would go here
        # For now, return raw (LZSS implementation is engine-specific)
        return raw
    
    return raw


def extract_all(archive: MPKArchive, output_dir: Path) -> List[Tuple[str, bool]]:
    """Extract all files from an MPK archive to a directory.
    
    Args:
        archive: Parsed MPK archive
        output_dir: Directory to extract to
    
    Returns:
        List of (filename, success) tuples
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    
    for entry in archive.entries:
        try:
            data = extract_file(archive, entry)
            out_path = output_dir / entry.filename
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(data)
            results.append((entry.filename, True))
        except Exception as e:
            results.append((entry.filename, False))
    
    return results


def pack_mpk(files: Dict[str, bytes], version: int = 1) -> bytes:
    """Pack files into an MPK archive.
    
    Args:
        files: Dict of {filename: file_data}
        version: MPK format version
    
    Returns:
        MPK archive bytes
    """
    # Build file table and data section
    entries = []
    data_section = bytearray()
    file_table = bytearray()
    
    for filename, file_data in files.items():
        offset = 16 + len(data_section)  # 16-byte header (placeholder for table offset)
        size = len(file_data)
        
        # No compression by default (can be enabled per-file)
        name_bytes = filename.encode("utf-8")
        
        entry = MPKEntry(
            filename=filename,
            offset=offset,
            size=size,
            compressed_size=0,
            compression=COMPRESSION_NONE,
        )
        entries.append(entry)
        data_section += file_data
        # Pad to 4-byte alignment
        pad = (4 - (len(data_section) % 4)) % 4
        data_section += b"\x00" * pad
    
    # Build file table
    for entry in entries:
        name_bytes = entry.filename.encode("utf-8")
        file_table += struct.pack("<I", entry.hash)
        file_table += struct.pack("<I", entry.offset)
        file_table += struct.pack("<I", entry.size)
        file_table += struct.pack("<I", entry.compressed_size)
        file_table += struct.pack("<H", 0)  # flags
        file_table += struct.pack("<H", len(name_bytes))
        file_table += name_bytes
        # Pad to 4 bytes
        pad = (4 - (len(file_table) % 4)) % 4
        file_table += b"\x00" * pad
    
    # Build header
    table_offset = 16  # Header size
    header = MPK_MAGIC
    header += struct.pack("<H", version)
    header += struct.pack("<I", len(entries))
    header += struct.pack("<I", table_offset)
    
    # Combine: header + file table + data
    return bytes(header) + bytes(file_table) + bytes(data_section)
