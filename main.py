#!/usr/bin/env python3
"""Entry point: fetch Giladiskon / Katalogpromosi promos for a date range.

Example:
    python main.py --start 2026-06-01 --end 2026-06-30
    python main.py --start 2026-06-01 --end 2026-06-30 --site giladiskon --output json
    python main.py --start 2026-06-01 --end 2026-06-30 --download-images ./promo_images
"""

from promo_scraper.cli import main

if __name__ == "__main__":
    main()
