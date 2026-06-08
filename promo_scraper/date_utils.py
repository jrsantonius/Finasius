"""Parsing of Indonesian promo date ranges such as those used by
Giladiskon and Katalogpromosi (e.g. "30 April - 13 Mei 2026",
"06-08 Maret 2026", "1 - 30 Juni 2026", "8 Juni 2026")."""

from __future__ import annotations

import re
from datetime import date

MONTHS = {
    "januari": 1, "jan": 1,
    "februari": 2, "feb": 2,
    "maret": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "ags": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10, "oct": 10,
    "november": 11, "nov": 11,
    "desember": 12, "des": 12, "dec": 12,
}

# "<day1> [<month1>] <sep> <day2> <month2> <year>"
_RANGE_RE = re.compile(
    r"(?P<d1>\d{1,2})\s*"
    r"(?:(?P<m1>[A-Za-z]+)\s*)?"
    r"[-–—]\s*"
    r"(?P<d2>\d{1,2})\s+"
    r"(?P<m2>[A-Za-z]+)\s+"
    r"(?P<year>\d{4})"
)

# Single date "<day> <month> <year>"
_SINGLE_RE = re.compile(
    r"(?P<d>\d{1,2})\s+(?P<m>[A-Za-z]+)\s+(?P<y>\d{4})"
)


def _month(name: str | None) -> int | None:
    if not name:
        return None
    return MONTHS.get(name.strip().lower())


def parse_date_range(text: str) -> tuple[date, date] | None:
    """Extract the first promo period found in ``text``.

    Returns a ``(start, end)`` tuple of :class:`datetime.date`, or ``None``
    if no recognizable date/range is present. When the range only carries
    one month name (e.g. "06-08 Maret 2026"), the missing month is assumed
    to be the same as the one that is present.
    """
    match = _RANGE_RE.search(text)
    if match:
        year = int(match.group("year"))
        month2 = _month(match.group("m2"))
        month1 = _month(match.group("m1")) or month2
        if month1 is None or month2 is None:
            return None
        day1 = int(match.group("d1"))
        day2 = int(match.group("d2"))
        try:
            start = date(year, month1, day1)
            end = date(year, month2, day2)
        except ValueError:
            return None
        if end < start:
            # Range spans a year boundary (e.g. "28 Desember - 3 Januari 2027")
            try:
                start = date(year - 1, month1, day1)
            except ValueError:
                return None
        return start, end

    match = _SINGLE_RE.search(text)
    if match:
        month = _month(match.group("m"))
        if month is None:
            return None
        try:
            day = int(match.group("d"))
            year = int(match.group("y"))
            d = date(year, month, day)
        except ValueError:
            return None
        return d, d

    return None


def ranges_overlap(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    """True if the closed intervals [a_start, a_end] and [b_start, b_end] overlap."""
    return a_start <= b_end and b_start <= a_end
