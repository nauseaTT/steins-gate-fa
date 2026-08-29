# Steins;Gate Persian Localization Project

ترجمه فارسی غیررسمی بازی Steins;Gate (نسخه PC/Steam)

A complete, engineered fan translation of the visual novel *Steins;Gate* from Japanese to Persian (Farsi).

## Quick Start

```bash
# Install the toolkit
cd sgp-toolkit
pip install -e .

# Export game scripts to JSON (requires extracted SCX files)
sgp export --input extracted/script/ --output extracted/strings/

# Import translated JSON back to SCX
sgp import --input extracted/strings/ --output build/script/ --original extracted/script/

# Validate translations
sgp validate --input extracted/strings/

# Test roundtrip integrity
sgp roundtrip --input extracted/script/sg01_01.scx

# Process Persian text (shaping + BiDi)
sgp shape --text "سلام، اوکابه رینتارو!"
```

## Project Structure

- `index.html` — Phase 1 interactive dashboard
- `docs/` — Full project documentation (master prompt, style guide, glossary, route matrix)
- `sgp-toolkit/` — Python toolkit for SCX/MPK parsing, encoding, shaping, validation
- `tools/` — Font generation, QA checkers, patch builder
- `config/` — Project configuration files

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 01 | Planning & analysis | ✅ Complete |
| 02 | Text extraction | 🔨 Tools ready |
| 03 | Conversion pipeline | 🔨 Tools ready |
| 04 | Translation platform | Pending |
| 05 | Main translation | Pending |
| 06 | Font engineering | 🔨 Tools ready |
| 07 | Repack & test | 🔨 Tools ready |
| 08 | Graphics & media | Pending |
| 09 | Full QA | 🔨 Tools ready |
| 10 | Package & release | 🔨 Tools ready |

## Legal

Non-commercial fan translation. Requires legitimate copy of STEINS;GATE. See [LICENSE.txt](LICENSE.txt).

---
*El Psy Kongroo // Divergence 1.048596%*
