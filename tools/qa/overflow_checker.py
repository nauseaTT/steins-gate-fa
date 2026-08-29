"""Text overflow checker — detects translated strings that exceed display limits.

Checks all translated strings against their character limits based on
string type (dialog, choice, phone, system, etc.) and flags those that
would overflow the game's text display boxes.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


# Maximum display characters per string type
LIMITS = {
    "dialog": 120,
    "choice": 30,
    "phone": 40,
    "system": 50,
    "tips": 80,
    "monologue": 120,
    "keyword": 20,  # Strict — triggers soft-lock
}


@dataclass
class OverflowIssue:
    """A text overflow issue."""
    string_id: int
    file: str
    text: str
    length: int
    limit: int
    flag_type: str
    severity: str  # "error" or "warning"


def compute_display_length(text: str) -> int:
    """Compute visible display length (excluding zero-width chars)."""
    cleaned = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\u2066\u2067\u2068\u2069]", "", text)
    return len(cleaned)


def check_overflow(
    translations_dir: str,
    max_expansion: float = 1.5,
) -> List[OverflowIssue]:
    """Check all translated strings for overflow.
    
    Args:
        translations_dir: Directory with translated JSON files
        max_expansion: Maximum allowed expansion ratio (FA length / JP length)
    
    Returns:
        List of OverflowIssue
    """
    issues = []
    
    for json_file in Path(translations_dir).glob("*.json"):
        if json_file.name.startswith("_"):
            continue
        
        data = json.loads(json_file.read_text(encoding="utf-8"))
        filename = data.get("file", json_file.name)
        
        for s in data.get("strings", []):
            fa_text = s.get("fa", "")
            if not fa_text:
                continue
            
            fa_len = compute_display_length(fa_text)
            jp_len = len(s.get("jp", ""))
            
            # Determine the applicable limit
            flags = s.get("flags", [])
            limit = max(LIMITS.get(f, 120) for f in flags) if flags else 120
            
            # Check absolute limit
            if fa_len > limit:
                severity = "error" if "keyword" in flags else "warning"
                issues.append(OverflowIssue(
                    string_id=s["id"],
                    file=filename,
                    text=fa_text[:50] + ("..." if len(fa_text) > 50 else ""),
                    length=fa_len,
                    limit=limit,
                    flag_type=", ".join(flags),
                    severity=severity,
                ))
            
            # Check expansion ratio
            elif jp_len > 0 and fa_len > jp_len * max_expansion:
                issues.append(OverflowIssue(
                    string_id=s["id"],
                    file=filename,
                    text=fa_text[:50] + ("..." if len(fa_text) > 50 else ""),
                    length=fa_len,
                    limit=int(jp_len * max_expansion),
                    flag_type=f"expansion (JP={jp_len})",
                    severity="warning",
                ))
    
    return issues


def generate_report(issues: List[OverflowIssue]) -> str:
    """Generate a human-readable overflow report."""
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    
    lines = [
        "Text Overflow Report",
        "=" * 50,
        f"Errors: {len(errors)}  |  Warnings: {len(warnings)}",
        "=" * 50,
        "",
    ]
    
    if errors:
        lines.append("ERRORS (will cause display issues):")
        for i in errors[:20]:  # Show first 20
            lines.append(f"  [{i.file}] ID {i.string_id}: {i.length}/{i.limit} chars ({i.flag_type})")
            lines.append(f"    \"{i.text}\"")
        if len(errors) > 20:
            lines.append(f"  ... and {len(errors) - 20} more errors")
        lines.append("")
    
    if warnings:
        lines.append("WARNINGS (review for readability):")
        for i in warnings[:20]:
            lines.append(f"  [{i.file}] ID {i.string_id}: {i.length}/{i.limit} chars ({i.flag_type})")
            lines.append(f"    \"{i.text}\"")
        if len(warnings) > 20:
            lines.append(f"  ... and {len(warnings) - 20} more warnings")
        lines.append("")
    
    if not errors and not warnings:
        lines.append("✅ No overflow issues found!")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    trans_dir = sys.argv[1] if len(sys.argv) > 1 else "extracted/strings"
    issues = check_overflow(trans_dir)
    print(generate_report(issues))
