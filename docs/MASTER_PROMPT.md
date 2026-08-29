# Steins;Gate Persian Localization Project — Master Prompt

## Project Identity

You are working on the **Steins;Gate Persian (Farsi) Fan Translation Project** — a complete, engineered localization of the PC/Steam visual novel *Steins;Gate* (original HD remaster, NOT Elite) from Japanese to Persian (Farsi).

- **Game:** STEINS;GATE (Steam App ID 412830 / GOG DRM-Free)
- **Engine:** MAGES. Engine (MagesEngine) — archives in `.mpk` (MPAK) format, scripts in `.scx` (compiled binary)
- **Source text encoding:** Shift-JIS (Japanese) / UTF-8 (English, Steam version is bilingual)
- **Target language:** Persian (Farsi) — right-to-left, requires Arabic script shaping
- **Estimated text volume:** ~50,000 strings / ~1.1 million Japanese words
- **Endings:** 6 (Mayuri, Faris, Luka, Moeka, Suzuha, True End — Kurisu)
- **Timeline:** 10 phases, ~6-9 months with a 3-5 person team

## Technical Architecture

### Core Pipeline (sgp-toolkit)

The project centers on a Python toolkit (`sgp-toolkit`) that handles the full roundtrip:

```
script.mpk → [MagesTool extract] → *.scx files
                                    ↓
                        [sgp-toolkit export] → JSON/TSV (JP + EN, with string IDs)
                                    ↓
                        [Weblate / Translation] → JSON/TSV (FA translations)
                                    ↓
                        [sgp-toolkit import] → Pre-shaped + Bidi-processed SCX
                                    ↓
                        [MagesTool repack] → script_fa.mpk
                                    ↓
                        [Replace in game folder] → Playable FA build
```

### Key Technical Solutions

1. **Encoding:** Hijack the English language slot (UTF-8 path) — inject Persian as UTF-8 (no BOM) via the existing English pipeline.

2. **RTL & Shaping:** Pre-shape Persian text with `arabic_reshaper` + apply BiDi with `python-bidi` BEFORE injecting into the game. The engine renders LTR, so we give it already-shaped, visually-ordered text.

3. **Font:** Generate a Bitmap Font from Vazirmatn (open-source) using FontForge + a Python Atlas Generator. Inject into `system.mpk` font table. Reduce dialog font size (32px → 26px) for text expansion.

4. **Phone Trigger Safety:** Validator checks all translated D-Mail keywords against the original character-count expectations. Mismatched trigger words cause soft-locks.

5. **Text Expansion:** Persian is 40-70% longer than Japanese. Solutions: smaller font, taller text box, manual line breaks, adaptive translation (shorter equivalents).

## 10-Phase Roadmap

| Phase | Title | Duration | Difficulty | Status |
|-------|-------|----------|------------|--------|
| 01 | Planning, game acquisition, structure analysis | 3-5 days | Easy | ✅ Complete |
| 02 | Extract raw scripts from MPK archives | 5-7 days | Medium | 🔨 In Progress |
| 03 | Build conversion pipeline (Parser + Export/Import) | 1-2 weeks | Hard | 🔨 In Progress |
| 04 | Translation platform setup (Weblate) + glossary | 3-4 days | Easy | Pending |
| 05 | Main translation (~1.1M words JP→FA) | 3-6 months | Hard | Pending |
| 06 | Font engineering, RTL, text box redesign | 2-3 weeks | Hard | Pending |
| 07 | Repack texts to SCX/MPK, test game execution | 1 week | Medium | Pending |
| 08 | UI image translation, menu graphics, video subtitles | 2 weeks | Medium | Pending |
| 09 | Full QA on all 6 endings + bug fixes | 3-4 weeks | Medium | Pending |
| 10 | Package installer, documentation, public release | 1 week | Easy | Pending |

**Critical path:** 1 → 2 → 3 → 5 → 7 → 9 → 10

## File Structure

```
steins-gate-fa/
├── index.html                    # Phase 1 dashboard (interactive)
├── docs/
│   ├── MASTER_PROMPT.md          # This file — full project spec
│   ├── STYLE_GUIDE.md            # Persian translation style guide
│   ├── GLOSSARY.md               # Mandatory term glossary
│   ├── ROUTE_MATRIX.md           # 6-ending decision matrix for QA
│   ├── SCX_FORMAT.md             # SCX binary format documentation
│   └── PHASE2_SPEC.md            # Phase 2 extraction specification
├── sgp-toolkit/                  # Python toolkit (pip-installable)
│   ├── setup.py
│   ├── sgp/
│   │   ├── __init__.py
│   │   ├── cli.py                # CLI entry point (export/import/validate)
│   │   ├── scx_parser.py         # SCX ↔ JSON bidirectional parser
│   │   ├── mpk_extractor.py      # MPK archive extractor/packer
│   │   ├── encoding.py           # Encoding normalizer (Shift-JIS ↔ UTF-8)
│   │   ├── shaping.py            # Pre-shaping + BiDi for Persian
│   │   ├── validator.py          # Phone Trigger keyword validator
│   │   ├── glossary.py           # Glossary consistency checker
│   │   └── config.py             # Configuration and paths
│   └── tests/
│       ├── test_scx_parser.py
│       ├── test_encoding.py
│       ├── test_shaping.py
│       └── test_validator.py
├── config/
│   ├── project.json              # Project configuration
│   └── font_config.json          # Font size and mapping config
├── tools/
│   ├── font/
│   │   ├── atlas_generator.py    # Bitmap font atlas generator
│   │   └── fontforge_export.py   # FontForge batch export script
│   ├── qa/
│   │   ├── route_matrix_checker.py
│   │   └── overflow_checker.py
│   └── repack/
│       └── build_patch.py        # Patch builder (xdelta)
├── extracted/                    # Extracted game files (gitignored)
├── assets_fa/                    # Persian-translated graphics
└── styles/                       # Translation style references
```

## Tools & Dependencies

- **Python 3.11+**: Core language for all tooling
- `arabic_reshaper`: Persian/Arabic letter shaping
- `python-bidi`: Bidirectional text reordering
- `charset-normalizer`: Encoding detection
- `struct`: Binary file parsing
- **MagesTool (Committee of Zero)**: MPK/SCX extraction and repacking
- **GARbro**: Multi-format archive explorer
- **FontForge**: Font editing and bitmap generation
- **Weblate**: Team translation management
- **Git + Git LFS**: Version control

## Legal & Ethical

This is a **non-commercial fan translation patch**. The final patch contains ONLY translated files — no original game assets are distributed. Users must own a legitimate copy of STEINS;GATE. Steins;Gate is property of MAGES. / Nitroplus.

---
*El Psy Kongroo // Divergence 1.048596%*
