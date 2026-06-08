from datetime import date

import pytest

from promo_scraper.date_utils import parse_date_range, ranges_overlap


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Promo Indomaret Katalog Terbaru 30 April - 13 Mei 2026",
         (date(2026, 4, 30), date(2026, 5, 13))),
        ("Promo JSM Toko Daging Nusantara periode 06-08 Maret 2026",
         (date(2026, 3, 6), date(2026, 3, 8))),
        ("Diskon kopi berlaku 1 - 30 Juni 2026 di seluruh outlet",
         (date(2026, 6, 1), date(2026, 6, 30))),
        ("Periode promo 16 Februari – 31 Maret 2026",
         (date(2026, 2, 16), date(2026, 3, 31))),
        ("Promo spesial tanggal 8 Juni 2026 saja",
         (date(2026, 6, 8), date(2026, 6, 8))),
    ],
)
def test_parse_date_range(text, expected):
    assert parse_date_range(text) == expected


def test_parse_date_range_returns_none_when_absent():
    assert parse_date_range("Promo KFC 2 Kupon Diskon Hingga 50%") is None


def test_parse_date_range_handles_year_wraparound():
    assert parse_date_range("Promo Tahun Baru 28 Desember - 2 Januari 2026") == (
        date(2025, 12, 28),
        date(2026, 1, 2),
    )


@pytest.mark.parametrize(
    "a_start, a_end, b_start, b_end, expected",
    [
        (date(2026, 6, 1), date(2026, 6, 30), date(2026, 6, 15), date(2026, 6, 20), True),
        (date(2026, 6, 1), date(2026, 6, 10), date(2026, 6, 10), date(2026, 6, 20), True),
        (date(2026, 6, 1), date(2026, 6, 10), date(2026, 6, 11), date(2026, 6, 20), False),
        (date(2026, 6, 11), date(2026, 6, 20), date(2026, 6, 1), date(2026, 6, 10), False),
    ],
)
def test_ranges_overlap(a_start, a_end, b_start, b_end, expected):
    assert ranges_overlap(a_start, a_end, b_start, b_end) is expected
