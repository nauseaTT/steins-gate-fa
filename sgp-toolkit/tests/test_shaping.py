"""Tests for Persian shaping and BiDi processing."""

import pytest
from sgp.shaping import (
    shape_text, apply_bidi, process_persian, is_persian, should_process,
    wrap_latin_segments, unshape_text,
)


def test_is_persian():
    """Test Persian text detection."""
    assert is_persian("سلام") is True
    assert is_persian("Hello") is False
    assert is_persian("سلام دنیا") is True
    assert is_persian("") is False
    assert is_persian("123") is False


def test_should_process():
    """Test process decision."""
    assert should_process("سلام") is True
    assert should_process("Hello") is False
    assert should_process("") is False
    assert should_process("   ") is False


def test_shape_text():
    """Test Arabic letter shaping."""
    shaped = shape_text("سلام")
    # Shaped text should be different from input (presentation forms)
    assert shaped != "سلام"
    # But should contain Arabic characters
    assert is_persian(shaped)


def test_apply_bidi():
    """Test BiDi visual reordering."""
    text = "سلام دنیا"
    visual = apply_bidi(text)
    # Visual order should be different from logical order for RTL text
    assert isinstance(visual, str)
    assert len(visual) > 0


def test_process_persian():
    """Test full Persian processing pipeline."""
    text = "سلام، اوکابه رینتارو!"
    result = process_persian(text)
    
    assert isinstance(result, str)
    assert len(result) > 0
    # Result should contain shaped Arabic characters
    assert is_persian(result)


def test_process_empty():
    """Test processing empty/whitespace text."""
    assert process_persian("") == ""
    assert process_persian("   ") == "   "


def test_process_no_persian():
    """Test processing non-Persian text (should pass through)."""
    text = "Hello World"
    # Non-Persian text won't be shaped, but will go through the pipeline
    result = process_persian(text, wrap_latin=False)
    assert isinstance(result, str)


def test_wrap_latin():
    """Test Latin segment wrapping."""
    text = "دی‌میل از SERN دریافت شد"
    result = wrap_latin_segments(text)
    # SERN should be wrapped in LRE/PDF embeddings
    assert "\u202a" in result  # LRE
    assert "\u202c" in result  # PDF
    assert "SERN" in result


def test_wrap_latin_multiple():
    """Test wrapping multiple Latin segments."""
    text = "D-Mail و IBN 5100"
    result = wrap_latin_segments(text)
    assert result.count("\u202a") >= 2  # At least 2 LRE marks


def test_unshape():
    """Test reverse shaping (lossy)."""
    text = "سلام"
    shaped = shape_text(text)
    unshaped = unshape_text(shaped)
    # NFKC normalization should bring it back to base forms
    # (may not be identical due to normalization, but should contain same base chars)
    assert is_persian(unshaped)


def test_process_with_latin_wrap():
    """Test full pipeline with Latin wrapping."""
    text = "دی‌میل از SERN دریافت شد"
    result = process_persian(text, wrap_latin=True)
    assert isinstance(result, str)
    assert len(result) > 0


def test_process_without_latin_wrap():
    """Test pipeline without Latin wrapping."""
    text = "سلام دنیا"
    result = process_persian(text, wrap_latin=False)
    assert isinstance(result, str)
    assert len(result) > 0
