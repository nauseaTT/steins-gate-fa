# Phase 2 Specification — Text Extraction

## Objective

Extract all localizable text strings from `script.mpk` and `system.mpk` into a structured, bilingual (JP+EN) JSON format with unique string IDs, ready for import into Weblate.

## Steps

### 2.1 Extract MPK Archives
```bash
# Using MagesTool (Committee of Zero)
magestool unpack script.mpk -o extracted/script/
magestool unpack system.mpk -o extracted/system/
```

### 2.2 Parse SCX Files
```bash
# Using sgp-toolkit
sgp export --input extracted/script/ --output extracted/strings/ --format json
```

### 2.3 Output Format

Each SCX file produces one JSON file:

```json
{
  "file": "sg01_01.scx",
  "version": 2,
  "string_count": 312,
  "strings": [
    {
      "id": 0,
      "speaker": "okabe",
      "flags": ["dialog"],
      "jp": "だから、今日までの──",
      "en": "So, up until today──",
      "fa": "",
      "context": "Opening monologue, Chapter 1",
      "char_limit": 40,
      "validated": false
    }
  ]
}
```

### 2.4 Checksum Test
- Modify one byte in a test SCX file
- Attempt to load in game
- If game crashes → checksum protection exists → patch needed
- If game loads fine → no checksum → safe to modify

### 2.5 Roundtrip Test
```bash
sgp export --input extracted/script/sg01_01.scx --output test.json
sgp import --input test.json --output test.scx
# Binary compare:
cmp extracted/script/sg01_01.scx test.scx
# Expected: files identical (no translations applied)
```

### 2.6 Deliverables
- `extracted/script/` — all SCX files from script.mpk
- `extracted/system/` — all SCX files from system.mpk  
- `extracted/strings/*.json` — structured bilingual strings
- `extracted/strings/_summary.json` — total string count, per-file breakdown
- `extracted/strings/_glossary_auto.json` — auto-extracted terms (names, locations)

## Risk Mitigation
- Always work on a copy, never the original game files
- Keep the Golden Master backup untouched
- Test one file fully before batch processing
