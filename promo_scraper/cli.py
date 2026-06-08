"""Command-line interface: fetch promos from Giladiskon and/or Katalogpromosi
within a chosen date range, showing the discount description and image."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
from datetime import date, datetime

from .date_utils import ranges_overlap
from .scraper import Promo, PromoScraper
from .sites import SITES, get_site

logger = logging.getLogger(__name__)


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Invalid date '{value}'. Use YYYY-MM-DD (e.g. 2026-06-01)."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch promo listings from Giladiskon and/or Katalogpromosi that "
            "are active within a chosen date range, including the discount "
            "description and promo image."
        )
    )
    parser.add_argument(
        "--start", required=True, type=_parse_date,
        help="Start of the date range, format YYYY-MM-DD (e.g. 2026-06-01)",
    )
    parser.add_argument(
        "--end", required=True, type=_parse_date,
        help="End of the date range, format YYYY-MM-DD (e.g. 2026-06-30)",
    )
    parser.add_argument(
        "--site", choices=[*SITES.keys(), "all"], default="all",
        help="Which site to scrape (default: all)",
    )
    parser.add_argument(
        "--max-pages", type=int, default=5,
        help="Maximum number of listing pages to crawl per site (default: 5)",
    )
    parser.add_argument(
        "--include-undated", action="store_true",
        help="Also include promos whose period could not be determined from the page",
    )
    parser.add_argument(
        "--output", choices=["table", "json", "csv"], default="table",
        help="Output format (default: table, printed to stdout)",
    )
    parser.add_argument(
        "--output-file",
        help="Write the result to this file instead of stdout (for json/csv)",
    )
    parser.add_argument(
        "--download-images",
        metavar="DIR",
        help="Download each matching promo's image into this directory",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging",
    )
    return parser


def _matches_range(promo: Promo, start: date, end: date, include_undated: bool) -> bool:
    if promo.period_start is None or promo.period_end is None:
        return include_undated
    return ranges_overlap(promo.period_start, promo.period_end, start, end)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug[:80] or "promo"


def _download_image(scraper: PromoScraper, promo: Promo, directory: str) -> str | None:
    if not promo.image_url:
        return None
    os.makedirs(directory, exist_ok=True)
    ext = os.path.splitext(promo.image_url.split("?")[0])[1] or ".jpg"
    filename = f"{_slugify(promo.site)}_{_slugify(promo.title)}{ext}"
    path = os.path.join(directory, filename)
    try:
        resp = scraper.session.get(promo.image_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - best-effort download
        logger.warning("Could not download image for '%s': %s", promo.title, exc)
        return None
    with open(path, "wb") as fh:
        fh.write(resp.content)
    return path


def _print_table(promos: list[Promo]) -> None:
    if not promos:
        print("No promos found in the selected date range.")
        return
    for promo in promos:
        period = "?"
        if promo.period_start and promo.period_end:
            if promo.period_start == promo.period_end:
                period = promo.period_start.strftime("%d %b %Y")
            else:
                period = (
                    f"{promo.period_start.strftime('%d %b %Y')} - "
                    f"{promo.period_end.strftime('%d %b %Y')}"
                )
        print("=" * 78)
        print(f"[{promo.site}] {promo.title}")
        print(f"Periode : {period}")
        print(f"URL     : {promo.url}")
        print(f"Gambar  : {promo.image_url or '-'}")
        desc = promo.description.strip()
        if len(desc) > 600:
            desc = desc[:600].rstrip() + "..."
        print("Keterangan diskon:")
        print(desc or "(tidak ada deskripsi)")
    print("=" * 78)
    print(f"Total: {len(promos)} promo")


def _write_json(promos: list[Promo], output_file: str | None) -> None:
    data = [p.to_dict() for p in promos]
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Wrote {len(promos)} promo(s) to {output_file}")
    else:
        print(text)


def _write_csv(promos: list[Promo], output_file: str | None) -> None:
    fieldnames = ["site", "title", "url", "image_url", "period_start", "period_end", "description"]
    fh = open(output_file, "w", newline="", encoding="utf-8") if output_file else sys.stdout
    try:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for promo in promos:
            writer.writerow(promo.to_dict())
    finally:
        if output_file:
            fh.close()
            print(f"Wrote {len(promos)} promo(s) to {output_file}")


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    if args.start > args.end:
        parser.error("--start must not be after --end")

    site_keys = list(SITES.keys()) if args.site == "all" else [args.site]

    scraper = PromoScraper()
    matched: list[Promo] = []

    for key in site_keys:
        config = get_site(key)
        logger.info("Scraping %s ...", config.name)
        for promo in scraper.iter_promos(config, max_pages=args.max_pages):
            if _matches_range(promo, args.start, args.end, args.include_undated):
                matched.append(promo)

    if args.download_images:
        for promo in matched:
            path = _download_image(scraper, promo, args.download_images)
            if path:
                logger.info("Saved image for '%s' -> %s", promo.title, path)

    if args.output == "table":
        _print_table(matched)
    elif args.output == "json":
        _write_json(matched, args.output_file)
    else:
        _write_csv(matched, args.output_file)

    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
