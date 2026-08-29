"""Persian text pre-shaping and BiDi processing.

This is the HEART of the Persian localization — without this, the MAGES. engine
(which renders LTR with no Arabic shaping support) would display disconnected
letters: م ح م د instead of محمد.

Pipeline:
1. arabic_reshaper.reshape() — connects letters into presentation forms
2. bidi.algorithm.get_display() — reorders for LTR rendering of RTL text
3. LRM/RLM marker injection — wraps Latin substrings for mixed-direction safety
"""

import re
from typing import Optional

try:
    import arabic_reshaper
except ImportError:
    arabic_reshaper = None

try:
    from bidi.algorithm import get_display
except ImportError:
    get_display = None


# Unicode control characters
LRM = "\u200e"  # Left-to-Right Mark
RLM = "\u200f"  # Right-to-Left Mark
LRE = "\u202a"  # Left-to-Right Embedding
RLE = "\u202b"  # Right-to-Left Embedding
PDF = "\u202c"  # Pop Directional Formatting
LRI = "\u2066"  # Left-to-Right Isolate
RLI = "\u2067"  # Right-to-Left Isolate
FSI = "\u2068"  # First Strong Isolate
PDI = "\u2069"  # Pop Directional Isolate

# Pattern for Latin/ASCII substrings within Persian text
LATIN_PATTERN = re.compile(
    r"[A-Za-z0-9]"
    r"(?:[A-Za-z0-9\s\-_.+*/()=!@#$%^&]*)"
    r"[A-Za-z0-9]"
)


def shape_text(text: str) -> str:
    """Apply Arabic/Persian letter shaping (connect letters).
    
    Transforms: 'سلام' (disconnected logical) → connected presentation forms.
    
    Requires: arabic_reshaper package
    """
    if arabic_reshaper is None:
        raise ImportError(
            "arabic_reshaper is required. Install with: pip install arabic-reshaper"
        )
    return arabic_reshaper.reshape(text)


def apply_bidi(text: str) -> str:
    """Apply BiDi algorithm for visual ordering.
    
    Reorders text so that an LTR renderer displays RTL text correctly.
    
    Requires: python-bidi package
    """
    if get_display is None:
        raise ImportError(
            "python-bidi is required. Install with: pip install python-bidi"
        )
    return get_display(text)


def wrap_latin_segments(text: str) -> str:
    """Wrap Latin/ASCII substrings with LRE/PDF embeddings for mixed-direction safety.
    
    Example: 'دی‌میل از SERN دریافت شد' → 'دی‌میل از ‪SERN‬ دریافت شد'
    This prevents the LTR Latin text from disrupting the RTL flow.
    
    Uses LRE/PDF (U+202A/U+202C) instead of LRI/PDI (U+2066/U+2069)
    because python-bidi doesn't support isolate characters.
    """
    def replacer(match):
        return f"{LRE}{match.group()}{PDF}"
    
    return LATIN_PATTERN.sub(replacer, text)


def process_persian(text: str, wrap_latin: bool = True) -> str:
    """Full Persian text processing pipeline for game injection.
    
    Steps:
    1. Wrap Latin substrings with directional isolates
    2. Shape letters (connect Arabic/Persian forms)
    3. Apply BiDi visual reordering
    
    The output is ready to be written as UTF-8 into the SCX file.
    The MAGES. engine will render it LTR, but the text will display
    correctly as RTL Persian.
    
    Args:
        text: Raw Persian text (logical order, unshaped)
        wrap_latin: Whether to wrap Latin substrings with isolates
    
    Returns:
        Processed text ready for game injection (visual order, shaped)
    """
    if not text or not text.strip():
        return text
    
    # Step 1: Wrap Latin segments
    if wrap_latin:
        text = wrap_latin_segments(text)
    
    # Step 2: Shape
    text = shape_text(text)
    
    # Step 3: BiDi
    text = apply_bidi(text)
    
    return text


def is_persian(text: str) -> bool:
    """Check if text contains Persian/Arabic characters."""
    for char in text:
        code = ord(char)
        # Arabic/Persian ranges
        if 0x0600 <= code <= 0x06FF:  # Arabic
            return True
        if 0xFB50 <= code <= 0xFDFF:  # Arabic Presentation Forms-A
            return True
        if 0xFE70 <= code <= 0xFEFF:  # Arabic Presentation Forms-B
            return True
        if 0x0660 <= code <= 0x0669:  # Arabic-Indic digits
            return True
    return False


def should_process(text: str) -> bool:
    """Determine if a string needs Persian processing."""
    return is_persian(text) and bool(text.strip())


# Reverse pipeline for roundtrip testing
def unshape_text(text: str) -> str:
    """Reverse the shaping process (for testing/debugging only).
    
    Note: This is a lossy reverse — presentation forms map back to
    base forms, but some contextual information may be lost.
    """
    # arabic_reshaper doesn't have a built-in reverse,
    # but for roundtrip testing we can use Unicode normalization
    import unicodedata
    # NFKC normalization decomposes presentation forms to base forms
    return unicodedata.normalize("NFKC", text)
