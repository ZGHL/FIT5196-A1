"""Pure text transformations required by the FIT5196 A1 public contract."""

from __future__ import annotations

import html
import re
import unicodedata

MISSING = "NaN"

_ORDER_RE = re.compile(r"(?<![A-Za-z0-9])(?:HORD|CORD)\d{6}(?![A-Za-z0-9])", re.I)
_SKU_RE = re.compile(r"(?<![A-Za-z0-9_-])SKU-[A-Za-z0-9]+(?![A-Za-z0-9_-])", re.I)
_PROMO_RE = re.compile(r"(?<![A-Za-z0-9_-])B[1-5]SAVE-\d{2}(?![A-Za-z0-9_-])", re.I)
_TAG_RE = re.compile(r"<[^<>]*>")
_URL_RE = re.compile(r"https?://[^\s<>]+|www\.[^\s<>]+", re.I)
_MARKER_RE = re.compile(
    r"\[(?:SYSTEM|CATALOGUE|VERIFIED_PURCHASE)\]"
    r"|\[SOURCE:\s*[^\]\r\n]*\]"
    r"|\[RATING:\s*[0-5]\s*/\s*5\]"
    r"|(?<![\w-])#verified-buyer(?![\w-])"
    r"|(?<![\w])@store_support(?![\w])",
    re.I,
)
_REFERENCE_WRAPPER_RE = re.compile(
    r"Reference:\s*(?:HORD|CORD)\d{6}\s*\|\s*SKU:\s*SKU-[A-Za-z0-9]+",
    re.I,
)
_PROMO_WRAPPER_RE = re.compile(r"PROMO:\s*B[1-5]SAVE-\d{2}", re.I)


def _normalise(value: object) -> str:
    if value is None:
        return ""
    return unicodedata.normalize("NFC", html.unescape(str(value)))


def _is_emoji(char: str) -> bool:
    """Identify pictographs/symbol emoji without deleting ordinary punctuation."""
    cp = ord(char)
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x27BF
        or 0xFE00 <= cp <= 0xFE0F
        or 0x1F1E6 <= cp <= 0x1F1FF
        or cp == 0x200D
    )


def clean_narrative_text(value):
    """Accept None or a string; return cleaned text or the string 'NaN'."""
    text = _normalise(value)
    text = _TAG_RE.sub(" ", text)
    text = _MARKER_RE.sub(" ", text)
    text = _URL_RE.sub(" ", text)
    text = "".join(" " if _is_emoji(c) else c for c in text)
    text = _REFERENCE_WRAPPER_RE.sub(" ", text)
    text = _PROMO_WRAPPER_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text if text else MISSING


def _extract(pattern: re.Pattern[str], value: object) -> str:
    match = pattern.search(_normalise(value))
    return match.group(0).upper() if match else MISSING


def extract_order_reference(value):
    """Accept None or a string; return the upper-case reference or 'NaN'."""
    return _extract(_ORDER_RE, value)


def extract_product_sku(value):
    """Accept None or a string; return the upper-case SKU or 'NaN'."""
    return _extract(_SKU_RE, value)


def extract_promo_code(value):
    """Accept None or a string; return the upper-case code or 'NaN'."""
    return _extract(_PROMO_RE, value)


def _is_latin_letter(char: str) -> bool:
    return unicodedata.category(char).startswith("L") and "LATIN" in unicodedata.name(char, "")


def build_latin_analysis(value):
    """Accept cleaned multilingual text; return Latin analysis or 'NaN'."""
    text = _normalise(value)
    if not text or text == MISSING:
        return MISSING
    kept = []
    has_latin = False
    for char in text:
        category = unicodedata.category(char)
        if category.startswith("L"):
            if _is_latin_letter(char):
                kept.append(char)
                has_latin = True
            else:
                kept.append(" ")
        elif _is_emoji(char):
            kept.append(" ")
        else:
            kept.append(char)
    result = re.sub(r"\s+", " ", "".join(kept)).strip()
    return result if has_latin and result else MISSING


def contains_non_latin_script(value):
    """Accept cleaned multilingual text; return a Python bool."""
    text = _normalise(value)
    if not text or text == MISSING:
        return False
    return any(
        unicodedata.category(char).startswith("L") and not _is_latin_letter(char)
        for char in text
    )
