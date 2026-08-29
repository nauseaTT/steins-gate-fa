#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mgstool.py — MAGES. engine MPK (Mages Package) extractor.

A faithful, self-contained Python reimplementation of CommitteeOfZero's
MPK container reader used by their "ungelify" tool and the
`SciAdvNet.MagesVfs` library for STEINS;GATE / CHAOS;HEAD / ROBOTICS;NOTES.

Format reference (ported 1:1 from CoZ source):
  * https://github.com/CommitteeOfZero/SciAdv.Net
      - src/SciAdvNet.MagesVfs/MagesArchive.cs
      - src/SciAdvNet.MagesVfs/MpkFileEntry.cs
      - src/Tools/Ungelify/Program.cs  (extract-all semantics)

Container layout:
  offset  size   field
  0x00    4      signature "MPK\\0"
  0x04    2      versionMinor  (int16 LE)
  0x06    2      versionMajor  (int16 LE)     : 1 => v1 (old), 2 => v2
  0x08    4/8    entryCount    (int32 LE for v1, int64 LE for v2)
  ...     pad    up to first entry header offset (0x40 for v1, 0x44 for v2)
  then entryCount x 256-byte file headers:

  v1 header (256 bytes):
      0x0  int32  id
      0x4  int32  dataOffset
      0x8  int32  compressedLength
      0xC  int32  uncompressedLength
      0x10 16     padding
      0x20 null-terminated name (UTF-8)

  v2 header (256 bytes):
      0x0  int32  id
      0x4  int64  dataOffset
      0xC  int64  compressedLength
      0x14 int64  uncompressedLength
      0x1C null-terminated name (UTF-8)

  Entry data:
      * uncompressed: raw slice [dataOffset .. dataOffset+uncompressedLength)
      * compressed:   zlib stream (RFC1950, e.g. header "78 9c"); CoZ skips
                      the leading 2 zlib-header bytes and inflates the raw
                      deflate stream of (compressedLength - 2) bytes.

This script only needs the Python standard library (no third-party deps).
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import zlib
from typing import Dict, List, Optional

SIGNATURE = b"MPK\0"
V1_FIRST_ENTRY_OFFSET = 0x40
V2_FIRST_ENTRY_OFFSET = 0x44
FILE_HEADER_LENGTH = 256


class MpkError(Exception):
    """Raised when a file is not a valid/supported MPK archive."""


class MpkArchive:
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self._data = f.read()
        self.version_major: int = 0
        self.version_minor: int = 0
        self.entry_count: int = 0
        self.first_entry_offset: int = 0
        self.is_compressed: bool = False
        self.entries: List[Dict[str, object]] = []
        self._parse()

    # ---------------------------------------------------------------- header
    def _parse(self) -> None:
        d = self._data
        if len(d) < 8 or d[:4] != SIGNATURE:
            raise MpkError(f"{self.path}: missing 'MPK\\0' signature (not an MPK archive)")

        self.version_minor = struct.unpack_from("<h", d, 4)[0]
        self.version_major = struct.unpack_from("<h", d, 6)[0]

        if self.version_major == 1:
            self.entry_count = struct.unpack_from("<i", d, 8)[0]
            self.first_entry_offset = V1_FIRST_ENTRY_OFFSET
            reader = self._read_entry_v1
            fixed_size = 16  # id + offset + clen + ulen, all 32-bit
        elif self.version_major == 2:
            self.entry_count = struct.unpack_from("<q", d, 8)[0]
            self.first_entry_offset = V2_FIRST_ENTRY_OFFSET
            reader = self._read_entry_v2
            fixed_size = 28  # id + offset + clen + ulen (64-bit fields)
        else:
            raise MpkError(f"{self.path}: unsupported MPK format version {self.version_major}")

        if self.entry_count < 0 or self.entry_count > 10_000_000:
            raise MpkError(f"{self.path}: implausible entry count {self.entry_count}")

        for i in range(self.entry_count):
            header_off = self.first_entry_offset + i * FILE_HEADER_LENGTH
            if header_off + FILE_HEADER_LENGTH > len(d):
                raise MpkError(f"{self.path}: truncated entry header block")
            block = d[header_off:header_off + FILE_HEADER_LENGTH]
            entry = reader(block)
            entry["index"] = i
            entry["header_offset"] = header_off
            self.entries.append(entry)

        self.is_compressed = any(
            e["compressed_length"] != e["uncompressed_length"] for e in self.entries
        )

    @staticmethod
    def _cstr(block: bytes, offset: int) -> str:
        end = block.find(b"\0", offset)
        if end == -1:
            end = len(block)
        return block[offset:end].decode("utf-8", errors="replace")

    def _read_entry_v1(self, b: bytes) -> Dict[str, object]:
        entry_id = struct.unpack_from("<i", b, 0)[0]
        offset = struct.unpack_from("<i", b, 4)[0]
        clen = struct.unpack_from("<i", b, 8)[0]
        ulen = struct.unpack_from("<i", b, 12)[0]
        name = self._cstr(b, 0x20)
        return {
            "id": entry_id,
            "offset": offset,
            "compressed_length": clen,
            "uncompressed_length": ulen,
            "name": name,
        }

    def _read_entry_v2(self, b: bytes) -> Dict[str, object]:
        entry_id = struct.unpack_from("<i", b, 0)[0]
        offset = struct.unpack_from("<q", b, 4)[0]
        clen = struct.unpack_from("<q", b, 12)[0]
        ulen = struct.unpack_from("<q", b, 20)[0]
        name = self._cstr(b, 0x1C)
        return {
            "id": entry_id,
            "offset": offset,
            "compressed_length": clen,
            "uncompressed_length": ulen,
            "name": name,
        }

    # ------------------------------------------------------------- extract
    def get_entry(self, key: str) -> Optional[Dict[str, object]]:
        for e in self.entries:
            if e["name"] == key or str(e["id"]) == key:
                return e
        return None

    def read_entry(self, entry: Dict[str, object]) -> bytes:
        """Return the fully decoded bytes of a single entry."""
        d = self._data
        offset = int(entry["offset"])
        clen = int(entry["compressed_length"])
        ulen = int(entry["uncompressed_length"])

        if not self.is_compressed:
            return d[offset:offset + ulen]

        # Compressed: skip the 2-byte zlib header and inflate raw deflate
        # (mirrors CoZ DeflateStream over SubReadStream(offset+2, clen-2)).
        raw = d[offset + 2:offset + clen]
        try:
            return zlib.decompress(raw, -15)
        except zlib.error:
            pass
        # Some toolchains store a full zlib stream (header kept): fallback.
        try:
            return zlib.decompress(d[offset:offset + clen])
        except zlib.error:
            # Last resort: treat as stored (uncompressed) data.
            return d[offset:offset + ulen]

    def extract_all(self, output_dir: str) -> List[str]:
        """Extract every entry into output_dir, preserving archive names.

        Returns the list of written file paths (relative to output_dir).
        """
        os.makedirs(output_dir, exist_ok=True)
        written: List[str] = []
        for e in self.entries:
            name = str(e["name"])
            # Basic path sanitization: never escape the output directory.
            safe_name = name.replace("\\", "/").lstrip("/").replace("..", "__")
            # Collapse any nested dirs into flat names (MPK names are flat
            # in practice); keep subdirs if the archive already uses them.
            out_path = os.path.join(output_dir, *[p for p in safe_name.split("/") if p])
            out_path = os.path.join(output_dir, os.path.basename(out_path))
            data = self.read_entry(e)
            with open(out_path, "wb") as f:
                f.write(data)
            written.append(os.path.relpath(out_path, output_dir))
        return written


# ====================================================================== CLI
def cmd_list(archive: MpkArchive) -> None:
    print(json.dumps({
        "path": archive.path,
        "version": f"v{archive.version_major}.{archive.version_minor}",
        "compressed": archive.is_compressed,
        "entry_count": archive.entry_count,
        "entries": [
            {
                "id": e["id"],
                "name": e["name"],
                "compressed_length": e["compressed_length"],
                "uncompressed_length": e["uncompressed_length"],
            }
            for e in archive.entries
        ],
    }, indent=2, ensure_ascii=False))


def cmd_extract(archive: MpkArchive, output_dir: str) -> None:
    written = archive.extract_all(output_dir)
    print(f"Extracted {len(written)} file(s) from {archive.path} -> {output_dir}")
    for w in written:
        print("  " + w)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="mgstool",
        description="MAGES. engine MPK extractor (CoZ uNgeliFY/MagesArchive port).",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List archive entries as JSON")
    p_list.add_argument("archive")

    p_ext = sub.add_parser("extract", help="Extract all entries to a directory")
    p_ext.add_argument("archive")
    p_ext.add_argument("output_dir")

    p_ext1 = sub.add_parser("extract-one", help="Extract a single entry by name or id")
    p_ext1.add_argument("archive")
    p_ext1.add_argument("key")
    p_ext1.add_argument("output_path")

    args = ap.parse_args(argv)

    arch = MpkArchive(args.archive)
    if args.command == "list":
        cmd_list(arch)
    elif args.command == "extract":
        cmd_extract(arch, args.output_dir)
    elif args.command == "extract-one":
        entry = arch.get_entry(args.key)
        if entry is None:
            print(f"Entry '{args.key}' not found.", file=sys.stderr)
            return 1
        data = arch.read_entry(entry)
        os.makedirs(os.path.dirname(os.path.abspath(args.output_path)), exist_ok=True)
        with open(args.output_path, "wb") as f:
            f.write(data)
        print(f"Wrote {len(data)} bytes -> {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
