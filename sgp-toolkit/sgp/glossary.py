"""Glossary consistency checker.

Ensures translated terms match the mandatory glossary throughout the project.
Detects inconsistencies in character names, technical terms, and locations.
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class GlossaryEntry:
    """A single glossary term."""
    jp: str
    en: str
    fa: str  # Mandatory Persian translation
    category: str = "general"  # general, character, location, concept, phone
    notes: str = ""


@dataclass 
class GlossaryViolation:
    """A glossary consistency violation."""
    string_id: int
    term_found: str  # What was found in the text
    expected: str  # What the glossary says it should be
    glossary_entry: GlossaryEntry
    severity: str = "error"  # error or warning


# Default glossary (synced with docs/GLOSSARY.md)
DEFAULT_GLOSSARY: List[GlossaryEntry] = [
    # Characters
    GlossaryEntry("岡部倫太郎", "Okabe Rintaro", "اوکابه رینتارو", "character"),
    GlossaryEntry("椎名まゆり", "Shiina Mayuri", "شینا مایوری", "character"),
    GlossaryEntry("牧瀬紅莉栖", "Makise Kurisu", "ماکاره کوریسو", "character"),
    GlossaryEntry("橋田至", "Hashida Itaru", "هاشیدا آیتارو", "character"),
    GlossaryEntry("阿万音鈴羽", "Amane Suzuha", "آمانه سوزوها", "character"),
    GlossaryEntry("桐生萌郁", "Kiryu Moeka", "کیریو موئکا", "character"),
    GlossaryEntry("漆原るか", "Urushibara Luka", "اوروشیبارا لوکا", "character"),
    GlossaryEntry("フェイリス", "Faris", "فریس", "character"),
    
    # Core concepts
    GlossaryEntry("世界線", "Worldline", "خط جهان", "concept"),
    GlossaryEntry("ダイアルアップ", "D-Mail", "دی‌میل", "concept"),
    GlossaryEntry("タイムリープ", "Time Leap", "جهش زمانی", "concept"),
    GlossaryEntry("読心", "Reading Steiner", "ریدینگ اشتاینر", "concept"),
    GlossaryEntry("ラボメン", "Lab Member", "عضو آزمایشگاه", "concept"),
    GlossaryEntry("未来ガジェット", "Future Gadget", "گجت آینده", "concept"),
    
    # Organizations
    GlossaryEntry("SERN", "SERN", "سرن", "concept"),
    
    # Locations
    GlossaryEntry("秋葉原", "Akihabara", "آکیهابارا", "location"),
    GlossaryEntry("ラジオ会館", "Radio Kaikan", "رادیو کایکان", "location"),
]


# Alternative spellings that should be flagged as violations
WRONG_SPELLINGS: Dict[str, str] = {
    # Wrong → Correct
    "اوکابه": "اوکابه رینتارو",  # Partial name
    "کوریسو": "ماکاره کوریسو",  # Missing surname
    "سوزوها": "آمانه سوزوها",  # Missing surname
    "موقکا": "کیریو موئکا",  # Wrong transliteration
    "لوکا": "اوروشیبارا لوکا",  # Missing surname
    "دی میل": "دی‌میل",  # Missing ZWNJ
    "دیمیل": "دی‌میل",  # Missing ZWNJ
    "خطкажdom": "خط جهان",  # Placeholder
    "جهش زمان": "جهش زمانی",  # Incomplete
    "ریدینگ استاینر": "ریدینگ اشتاینر",  # Wrong transliteration
}


def load_glossary(path: str = "config/glossary.json") -> List[GlossaryEntry]:
    """Load glossary from JSON file, falling back to defaults."""
    p = Path(path)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return [
            GlossaryEntry(
                jp=item["jp"],
                en=item["en"],
                fa=item["fa"],
                category=item.get("category", "general"),
                notes=item.get("notes", ""),
            )
            for item in data
        ]
    return DEFAULT_GLOSSARY


def check_text(
    text: str,
    glossary: List[GlossaryEntry],
    string_id: int = -1,
) -> List[GlossaryViolation]:
    """Check a single text string for glossary violations.
    
    Args:
        text: Persian translated text
        glossary: Glossary entries to check against
        string_id: String ID for reference
    
    Returns:
        List of violations found in the text
    """
    violations = []
    
    # Check for wrong spellings
    for wrong, correct in WRONG_SPELLINGS.items():
        if wrong in text:
            # Find the matching glossary entry
            entry = next(
                (g for g in glossary if g.fa == correct),
                GlossaryEntry("", "", correct, "general"),
            )
            violations.append(GlossaryViolation(
                string_id=string_id,
                term_found=wrong,
                expected=correct,
                glossary_entry=entry,
                severity="error",
            ))
    
    # Check for inconsistent character name usage
    # (e.g., using English name when Persian is mandatory)
    for entry in glossary:
        if entry.en and entry.en in text and entry.fa and entry.fa not in text:
            # English term found but Persian equivalent not used
            # This is OK for proper nouns like "SERN" or "D-Mail"
            if entry.category in ("character", "location") and entry.en not in ("SERN", "IBN 5100"):
                violations.append(GlossaryViolation(
                    string_id=string_id,
                    term_found=entry.en,
                    expected=entry.fa,
                    glossary_entry=entry,
                    severity="warning",
                ))
    
    return violations


def check_all(
    translations: Dict[int, str],
    glossary: Optional[List[GlossaryEntry]] = None,
) -> List[GlossaryViolation]:
    """Check all translations for glossary consistency.
    
    Args:
        translations: Dict of {string_id: persian_text}
        glossary: Glossary to use (loads default if None)
    
    Returns:
        List of all violations
    """
    if glossary is None:
        glossary = load_glossary()
    
    all_violations = []
    for string_id, text in translations.items():
        violations = check_text(text, glossary, string_id)
        all_violations.extend(violations)
    
    return all_violations


def generate_report(violations: List[GlossaryViolation]) -> str:
    """Generate a human-readable glossary report."""
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]
    
    lines = [
        f"Glossary Consistency Report",
        f"{'='*50}",
        f"Errors: {len(errors)}  |  Warnings: {len(warnings)}",
        f"{'='*50}",
        "",
    ]
    
    if errors:
        lines.append("ERRORS (must fix):")
        for v in errors:
            lines.append(f"  [ID {v.string_id}] Found: '{v.term_found}' → Expected: '{v.expected}'")
        lines.append("")
    
    if warnings:
        lines.append("WARNINGS (review):")
        for v in warnings:
            lines.append(f"  [ID {v.string_id}] Found: '{v.term_found}' → Expected: '{v.expected}'")
        lines.append("")
    
    if not errors and not warnings:
        lines.append("✅ No glossary violations found!")
    
    return "\n".join(lines)
