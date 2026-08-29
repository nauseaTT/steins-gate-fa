"""Route Matrix checker for QA — validates all 6 ending paths are accessible.

This tool checks that all D-Mail trigger keywords required for each ending
are properly translated and validated. It cross-references the route matrix
with the trigger keyword table and translation files.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


# Route definitions (from docs/ROUTE_MATRIX.md)
ROUTES = {
    "mayuri": {
        "name": "Mayuri Ending",
        "strategy": "no_reply",
        "trigger_ids": [],  # No D-Mails to reply to
    },
    "faris": {
        "name": "Faris Ending",
        "strategy": "reply_only",
        "trigger_ids": [],  # Populated from trigger_keywords.json
        "character": "faris",
    },
    "luka": {
        "name": "Luka Ending",
        "strategy": "reply_only",
        "trigger_ids": [],
        "character": "luka",
    },
    "moeka": {
        "name": "Moeka Ending",
        "strategy": "reply_only",
        "trigger_ids": [],
        "character": "moeka",
    },
    "suzuha": {
        "name": "Suzuha Ending",
        "strategy": "reply_only",
        "trigger_ids": [],
        "character": "suzuha",
    },
    "true_end": {
        "name": "True Ending (Kurisu)",
        "strategy": "clear_all_flags",
        "trigger_ids": [],
        "character": "kurisu",
    },
}


@dataclass
class RouteCheckResult:
    """Result of checking a single route."""
    route_id: str
    route_name: str
    accessible: bool
    issues: List[str] = field(default_factory=list)
    triggers_checked: int = 0
    triggers_valid: int = 0


def check_routes(
    translations_dir: str,
    trigger_table_path: str = "config/trigger_keywords.json",
) -> List[RouteCheckResult]:
    """Check all routes for accessibility.
    
    Args:
        translations_dir: Directory containing translated JSON files
        trigger_table_path: Path to trigger keyword table
    
    Returns:
        List of RouteCheckResult for each route
    """
    # Load trigger table
    trigger_path = Path(trigger_table_path)
    if not trigger_path.exists():
        return [
            RouteCheckResult(
                route_id=rid,
                route_name=route["name"],
                accessible=False,
                issues=["Trigger keyword table not found — cannot validate route"],
            )
            for rid, route in ROUTES.items()
        ]
    
    trigger_table = json.loads(trigger_path.read_text(encoding="utf-8"))
    
    # Load all translations
    translations = {}
    for json_file in Path(translations_dir).glob("*.json"):
        if json_file.name.startswith("_"):
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        for s in data.get("strings", []):
            if s.get("fa"):
                translations[s["id"]] = s["fa"]
    
    results = []
    
    for route_id, route in ROUTES.items():
        result = RouteCheckResult(
            route_id=route_id,
            route_name=route["name"],
            accessible=True,
        )
        
        if route["strategy"] == "no_reply":
            # Mayuri ending: no triggers needed
            result.triggers_checked = 0
            result.triggers_valid = 0
            result.issues.append("✅ No D-Mail replies needed — always accessible")
        
        else:
            # Check all triggers for this route
            route_triggers = [
                t for t in trigger_table
                if t.get("route") == route_id or t.get("character") == route.get("character")
            ]
            
            result.triggers_checked = len(route_triggers)
            
            for trigger in route_triggers:
                trigger_id = trigger["id"]
                fa_text = translations.get(trigger_id, "")
                
                if not fa_text:
                    result.accessible = False
                    result.issues.append(
                        f"Trigger #{trigger_id} not translated — route may soft-lock"
                    )
                elif len(fa_text) > trigger.get("max_chars", 40):
                    result.accessible = False
                    result.issues.append(
                        f"Trigger #{trigger_id} too long ({len(fa_text)} > {trigger['max_chars']}) — soft-lock risk"
                    )
                else:
                    result.triggers_valid += 1
            
            if result.triggers_checked > 0 and result.triggers_valid == result.triggers_checked:
                result.issues.append(f"✅ All {result.triggers_checked} triggers valid")
        
        results.append(result)
    
    return results


def generate_report(results: List[RouteCheckResult]) -> str:
    """Generate a human-readable route accessibility report."""
    lines = [
        "Route Accessibility Report",
        "=" * 50,
        "",
    ]
    
    all_accessible = all(r.accessible for r in results)
    
    for r in results:
        status = "✅" if r.accessible else "❌"
        lines.append(f"{status} {r.route_name} ({r.triggers_valid}/{r.triggers_checked} triggers)")
        for issue in r.issues:
            lines.append(f"   {issue}")
        lines.append("")
    
    if all_accessible:
        lines.append("✅ All 6 endings are accessible!")
    else:
        blocked = sum(1 for r in results if not r.accessible)
        lines.append(f"❌ {blocked} ending(s) have accessibility issues!")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    trans_dir = sys.argv[1] if len(sys.argv) > 1 else "extracted/strings"
    results = check_routes(trans_dir)
    print(generate_report(results))
