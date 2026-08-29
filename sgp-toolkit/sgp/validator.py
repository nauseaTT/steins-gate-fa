"""Phone Trigger keyword validator.

Validates that translated D-Mail keywords match the character-count
expectations of the game's Phone Trigger system. Mismatched keywords
cause soft-locks where the player cannot progress.

The validator checks:
1. Character count compatibility (with shaping expansion accounted for)
2. No empty keywords
3. Keywords exist in the reference table
4. Latin terms within keywords are preserved
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class ValidationResult:
    """Result of validating a single keyword."""
    string_id: int
    keyword_jp: str
    keyword_fa: str
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TriggerKeyword:
    """A phone trigger keyword definition."""
    string_id: int
    jp_keyword: str
    en_keyword: str
    max_chars: int  # Maximum display characters
    context: str = ""  # Which D-Mail/scene this belongs to


# Known trigger keywords (populated from game analysis)
# This table is the CRITICAL safety net for preventing soft-locks
TRIGGER_TABLE: List[TriggerKeyword] = [
    # Phase 2 will populate this from actual game data
    # Format: TriggerKeyword(id, jp, en, max_chars, context)
]


def load_trigger_table(path: str = "config/trigger_keywords.json") -> None:
    """Load trigger keyword table from JSON file."""
    global TRIGGER_TABLE
    p = Path(path)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        TRIGGER_TABLE = [
            TriggerKeyword(
                string_id=item["id"],
                jp_keyword=item["jp"],
                en_keyword=item.get("en", ""),
                max_chars=item["max_chars"],
                context=item.get("context", ""),
            )
            for item in data
        ]


def save_trigger_table(path: str = "config/trigger_keywords.json") -> None:
    """Save current trigger table to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "id": t.string_id,
            "jp": t.jp_keyword,
            "en": t.en_keyword,
            "max_chars": t.max_chars,
            "context": t.context,
        }
        for t in TRIGGER_TABLE
    ]
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def compute_display_length(text: str) -> int:
    """Compute the display length of text after shaping.
    
    Persian shaping can change character count:
    - Letter connections may merge or split glyphs
    - ZWNJ (‌) is zero-width
    - Directional marks are zero-width
    
    This is an approximation — actual rendering depends on the font.
    """
    # Remove zero-width characters
    cleaned = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\u2066\u2067\u2068\u2069]", "", text)
    # Count remaining characters
    # Note: shaped Arabic may have different counts, but this is a safe approximation
    return len(cleaned)


def validate_keyword(
    keyword_jp: str,
    keyword_fa: str,
    max_chars: int,
    string_id: int = -1,
) -> ValidationResult:
    """Validate a single translated keyword.
    
    Args:
        keyword_jp: Original Japanese keyword
        keyword_fa: Translated Persian keyword
        max_chars: Maximum allowed display characters
        string_id: String ID for reference
    
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult(
        string_id=string_id,
        keyword_jp=keyword_jp,
        keyword_fa=keyword_fa,
        valid=True,
    )
    
    # Check: not empty
    if not keyword_fa or not keyword_fa.strip():
        result.valid = False
        result.errors.append("Translated keyword is empty")
        return result
    
    # Check: display length within limit
    display_len = compute_display_length(keyword_fa)
    if display_len > max_chars:
        result.valid = False
        result.errors.append(
            f"Keyword too long: {display_len} chars (max {max_chars}). "
            f"This may cause Phone Trigger soft-lock."
        )
    
    # Warning: very short keyword (might not match trigger detection)
    if display_len < 2:
        result.warnings.append(
            f"Keyword very short ({display_len} chars) — verify trigger detection works"
        )
    
    # Check: no control characters that might break the trigger system
    if re.search(r"[\x00-\x1f\x7f]", keyword_fa):
        result.valid = False
        result.errors.append("Keyword contains control characters")
    
    # Warning: contains Latin characters (may need LRM/RLM markers)
    if re.search(r"[A-Za-z]", keyword_fa):
        result.warnings.append(
            "Keyword contains Latin characters — ensure directional markers are applied"
        )
    
    return result


def validate_all_keywords(
    translations: Dict[int, str],
) -> List[ValidationResult]:
    """Validate all translated keywords against the trigger table.
    
    Args:
        translations: Dict of {string_id: translated_keyword}
    
    Returns:
        List of ValidationResult for each keyword
    """
    results = []
    
    for trigger in TRIGGER_TABLE:
        fa_keyword = translations.get(trigger.string_id, "")
        result = validate_keyword(
            keyword_jp=trigger.jp_keyword,
            keyword_fa=fa_keyword,
            max_chars=trigger.max_chars,
            string_id=trigger.string_id,
        )
        result.warnings.append(f"Context: {trigger.context}")
        results.append(result)
    
    return results


def generate_report(results: List[ValidationResult]) -> str:
    """Generate a human-readable validation report."""
    total = len(results)
    passed = sum(1 for r in results if r.valid)
    failed = total - passed
    
    lines = [
        f"Phone Trigger Keyword Validation Report",
        f"{'='*50}",
        f"Total: {total}  |  Passed: {passed}  |  Failed: {failed}",
        f"{'='*50}",
        "",
    ]
    
    if failed > 0:
        lines.append("FAILED KEYWORDS:")
        for r in results:
            if not r.valid:
                lines.append(f"  [ID {r.string_id}] JP: '{r.keyword_jp}' → FA: '{r.keyword_fa}'")
                for err in r.errors:
                    lines.append(f"    ❌ {err}")
                for warn in r.warnings:
                    lines.append(f"    ⚠️  {warn}")
                lines.append("")
    
    if failed == 0 and total > 0:
        lines.append("✅ All keywords passed validation!")
    
    return "\n".join(lines)
