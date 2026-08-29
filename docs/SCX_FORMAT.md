# SCX Binary Format Documentation

## Overview

SCX (Script Compiled eXecutable) is the compiled script format used by MAGES. Engine. Each `.scx` file contains dialog text, branching logic, phone trigger data, and system commands in a binary structure.

## File Header

```
Offset  Size  Field           Description
0x00    4     Magic           "SCX\0" or version-specific magic
0x04    2     Version         Format version (varies by game build)
0x06    2     Header Size     Size of header section
0x08    4     String Count    Number of text strings in the file
0x0C    4     String Offset   Offset to string table
0x10    4     Script Offset   Offset to command bytecode
0x14    4     Checksum        Simple checksum (XOR or additive)
```

## String Table

The string table contains all localizable text strings. Each entry:

```
Offset  Size  Field           Description
+0      4     String ID       Unique identifier (sequential or hashed)
+4      4     String Length   Byte length of string (not char count)
+8      4     Speaker ID      Character ID (0 = narrator/system)
+12     4     Flags           Bit flags: [0]=dialog [1]=choice [2]=phone [3]=system
+16     N     String Data     Raw bytes in source encoding (Shift-JIS or UTF-8)
```

### String Flags

| Bit | Mask | Meaning |
|-----|------|---------|
| 0   | 0x01 | Dialog text |
| 1   | 0x02 | Choice option |
| 2   | 0x04 | Phone/D-Mail text |
| 3   | 0x08 | System/UI text |
| 4   | 0x10 | TIPs entry |
| 5   | 0x20 | Monologue (inner thought) |
| 6   | 0x40 | Requires keyword validation |

## Command Bytecode

After the string table, the script contains compiled commands that control:
- Text display (show string by ID)
- Character sprite changes
- Background transitions
- Branch points (jump to offset on condition)
- Phone trigger activation
- Sound/voice playback

Commands are NOT translated — only string table entries are modified.

## Encoding Notes

- Japanese version: strings in **Shift-JIS** (cp932)
- English version (Steam): strings in **UTF-8** (no BOM)
- For Persian: inject UTF-8 into the English language slot
- **CRITICAL:** Never write BOM (EF BB BF) — MAGES. parser treats it as text content

## Roundtrip Integrity

The export/import cycle MUST produce byte-identical output when no translations are applied:
1. Parse SCX → export to JSON
2. Import JSON → write SCX
3. Binary compare original and output
4. If any byte differs, the parser has a bug

This "roundtrip test" is the primary validation for the toolkit.
