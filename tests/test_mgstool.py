#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automated verification for the MagesTool (tools/mgstool.py).

Validates the MPK reader against CommitteeOfZero's own official test archives
(tests/fixtures/*.mpk from https://github.com/CommitteeOfZero/SciAdv.Net),
asserting:
  * correct container parsing (v1 compressed / v2 uncompressed),
  * correct entry counts and names,
  * correct decompression, and
  * a valid SC3 script signature ("SC3\\0") at the start of every extracted
    SCX/SCR file.

Run with the standard-library runner (no third-party deps):
    python3 tests/test_mgstool.py
"""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from mgstool import MpkArchive, MpkError  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")
SC3_SIGNATURE = b"SC3\x00"


class MpkParsingTests(unittest.TestCase):
    def test_v1_compressed_parsing(self):
        arch = MpkArchive(os.path.join(FIXTURES, "CompressedV1.mpk"))
        self.assertEqual(arch.version_major, 1)
        self.assertTrue(arch.is_compressed)
        self.assertEqual(arch.entry_count, 94)
        self.assertTrue(all(e["name"].lower().endswith(".scr") for e in arch.entries))
        # spot-check a known entry
        self.assertIn("_Startup.scr", [e["name"] for e in arch.entries])

    def test_v2_uncompressed_parsing(self):
        arch = MpkArchive(os.path.join(FIXTURES, "UncompressedV2.mpk"))
        self.assertEqual(arch.version_major, 2)
        self.assertFalse(arch.is_compressed)
        self.assertEqual(arch.entry_count, 216)
        self.assertTrue(all(e["name"].lower().endswith(".scx") for e in arch.entries))
        self.assertIn("_map.scx", [e["name"] for e in arch.entries])

    def test_rejects_non_mpk(self):
        with tempfile.TemporaryDirectory() as td:
            bogus = os.path.join(td, "not_mpk.bin")
            with open(bogus, "wb") as f:
                f.write(b"HELLO WORLD" * 100)
            with self.assertRaises(MpkError):
                MpkArchive(bogus)


class ExtractionTests(unittest.TestCase):
    def _extract_and_assert_sc3(self, mpk_name, expected_count, expected_ext):
        with tempfile.TemporaryDirectory() as td:
            arch = MpkArchive(os.path.join(FIXTURES, mpk_name))
            written = arch.extract_all(td)
            self.assertEqual(len(written), expected_count)
            for rel in written:
                self.assertTrue(rel.lower().endswith(expected_ext))
                with open(os.path.join(td, rel), "rb") as f:
                    self.assertEqual(f.read(4), SC3_SIGNATURE,
                                     f"{rel} does not start with SC3 signature")

    def test_v1_extract_all_compressed(self):
        self._extract_and_assert_sc3("CompressedV1.mpk", 94, ".scr")

    def test_v2_extract_all_uncompressed(self):
        self._extract_and_assert_sc3("UncompressedV2.mpk", 216, ".scx")


if __name__ == "__main__":
    unittest.main(verbosity=2)
