"""Tests for Phone Trigger keyword validator."""

import pytest
from sgp.validator import (
    validate_keyword, validate_all_keywords, generate_report,
    compute_display_length, ValidationResult, TriggerKeyword,
    TRIGGER_TABLE, load_trigger_table, save_trigger_table,
)


def test_compute_display_length():
    """Test display length computation."""
    assert compute_display_length("سلام") == 4
    assert compute_display_length("Hello") == 5
    assert compute_display_length("") == 0
    # ZWNJ is zero-width (د ی م ی ل = 5 visible chars)
    assert compute_display_length("دی\u200cمیل") == 5


def test_validate_keyword_ok():
    """Test validation of a valid keyword."""
    result = validate_keyword("キーワード", "کلمه", max_chars=20)
    assert result.valid is True
    assert len(result.errors) == 0


def test_validate_keyword_empty():
    """Test validation of empty keyword."""
    result = validate_keyword("キーワード", "", max_chars=20)
    assert result.valid is False
    assert any("empty" in e for e in result.errors)


def test_validate_keyword_too_long():
    """Test validation of oversized keyword."""
    long_keyword = "این یک کلمه کلیدی بسیار طولانی است که از حد مجاز عبور می‌کند"
    result = validate_keyword("キーワード", long_keyword, max_chars=10)
    assert result.valid is False
    assert any("too long" in e.lower() for e in result.errors)


def test_validate_keyword_control_chars():
    """Test detection of control characters."""
    result = validate_keyword("キーワード", "کلمه\x00نامعتبر", max_chars=20)
    assert result.valid is False
    assert any("control" in e.lower() for e in result.errors)


def test_validate_keyword_latin_warning():
    """Test warning for Latin characters in keyword."""
    result = validate_keyword("キーワード", "D-Mail", max_chars=20)
    assert result.valid is True
    assert any("Latin" in w or "latin" in w for w in result.warnings)


def test_validate_all_keywords():
    """Test batch validation with trigger table."""
    # Set up a temporary trigger table
    import sgp.validator as v
    original_table = v.TRIGGER_TABLE
    v.TRIGGER_TABLE = [
        TriggerKeyword(1, "キーワード", "keyword", 10, "test context"),
        TriggerKeyword(2, "返信", "reply", 5, "test reply"),
    ]
    
    try:
        translations = {1: "کلمه", 2: "پاسخ"}
        results = validate_all_keywords(translations)
        assert len(results) == 2
        assert all(r.valid for r in results)
    finally:
        v.TRIGGER_TABLE = original_table


def test_generate_report():
    """Test report generation."""
    results = [
        ValidationResult(1, "キーワード", "کلمه", valid=True),
        ValidationResult(2, "返信", "", valid=False, errors=["Translated keyword is empty"]),
    ]
    report = generate_report(results)
    assert "Validation Report" in report
    assert "Failed: 1" in report
    assert "FAILED" in report


def test_save_load_trigger_table(tmp_path):
    """Test saving and loading trigger table."""
    import sgp.validator as v
    
    # Set up temp table
    v.TRIGGER_TABLE = [
        TriggerKeyword(1, "テスト", "test", 10, "test"),
    ]
    
    path = str(tmp_path / "trigger.json")
    save_trigger_table(path)
    
    # Clear and reload
    v.TRIGGER_TABLE = []
    load_trigger_table(path)
    
    assert len(v.TRIGGER_TABLE) == 1
    assert v.TRIGGER_TABLE[0].jp_keyword == "テスト"
