"""Pure parsing helpers for Leboncoin ads (no Playwright dependency).

Keeps the gateway thin and lets us unit-test the tricky regex/keyword logic.
"""

from __future__ import annotations

import re

from src.domain.vehicle import Autopilot, Paint, Trim

_AUTOPILOT_EAP_PATTERNS = [
    # Canonical and common LBC mistypes: "amélioré" → "améloiré".
    r"autopilot\s+am[ée]l(?:io|oi)r[ée]",
    r"pilotage\s+automatique\s+am[ée]l(?:io|oi)r[ée]",
    r"\benhanced\s+autopilot\b",
    r"\beap\b",
    r"\bap\s+am[ée]l(?:io|oi)r[ée]\b",
]

_AUTOPILOT_FSD_PATTERNS = [
    r"\bfsd\b",
    r"full[\s-]self[\s-]driving",
    r"capacit[ée]\s+de\s+conduite\s+enti[èe]rement\s+autonome",
    r"conduite\s+enti[èe]rement\s+autonome",
]

_PAINT_BLACK_PATTERNS = [
    r"\bnoir(?:e|s|es)?\b",
    r"\bsolid\s+black\b",
    r"\bpearl\s+black\b",
    r"\bblack\s+m[ée]tallis[ée]\b",
]

_PAINT_WHITE_PATTERNS = [
    r"\bblanc(?:he|s|hes)?\b",
    r"\bpearl\s+white\b",
    r"\bwhite\b",
]

_TRIM_AWD_PATTERNS: list[tuple[re.Pattern[str], Trim]] = [
    (re.compile(r"\bperformance\b", re.IGNORECASE), Trim.PAWD),
    (re.compile(r"\bpremium\b", re.IGNORECASE), Trim.PRAWD),
    (re.compile(r"\blong[\s-]?range\b|\bgrande\s+autonomie\b", re.IGNORECASE), Trim.LRAWD),
]


def detect_autopilot(text: str) -> Autopilot:
    """Map ad body text to an Autopilot level. FSD beats EAP."""
    lower = text.lower()
    for pattern in _AUTOPILOT_FSD_PATTERNS:
        if re.search(pattern, lower):
            return Autopilot.FSD
    for pattern in _AUTOPILOT_EAP_PATTERNS:
        if re.search(pattern, lower):
            return Autopilot.ENHANCED
    return Autopilot.BASIC


def detect_paint(text: str) -> Paint:
    """Map ad body text to a Paint color."""
    lower = text.lower()
    for pattern in _PAINT_BLACK_PATTERNS:
        if re.search(pattern, lower):
            return Paint.BLACK
    for pattern in _PAINT_WHITE_PATTERNS:
        if re.search(pattern, lower):
            return Paint.WHITE
    return Paint.OTHER


def detect_trim(text: str) -> Trim | None:
    """Map subject / u_car_version to a Trim. Requires AWD/Dual Motor mention."""
    lower = text.lower()
    is_awd = bool(re.search(r"\bawd\b|\bdual\s*motor\b|transmission\s+int[ée]grale", lower))
    if not is_awd:
        # If no AWD hint, we can't tell if it's PRAWD vs LRAWD or RWD. Reject.
        return None

    for pattern, trim in _TRIM_AWD_PATTERNS:
        if pattern.search(lower):
            return trim
    return None


def parse_int(text: str) -> int | None:
    """Extract first integer from a string like '92500 km' or '40 100'."""
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None
