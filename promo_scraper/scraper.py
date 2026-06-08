"""Generic listing/article scraper driven by :mod:`promo_scraper.sites`."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .date_utils import parse_date_range
from .sites import SiteConfig

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

REQUEST_TIMEOUT = 20


@dataclass
class Promo:
    site: str
    title: str
    url: str
    image_url: str | None
    description: str
    period_start: date | None
    period_end: date | None
    raw_period_text: str | None = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "site": self.site,
            "title": self.title,
            "url": self.url,
            "image_url": self.image_url,
            "description": self.description,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


class PromoScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)

    # -- network -----------------------------------------------------
    def fetch(self, url: str) -> BeautifulSoup | None:
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)
            return None
        return BeautifulSoup(resp.text, "lxml")

    # -- parsing ------------------------------------------------------
    @staticmethod
    def _absolute(base_url: str, src: str | None) -> str | None:
        if not src:
            return None
        return urljoin(base_url, src)

    @staticmethod
    def _best_image(img_tag) -> str | None:
        if img_tag is None:
            return None
        for attr in ("data-src", "data-lazy-src", "src", "data-srcset", "srcset"):
            value = img_tag.get(attr)
            if value:
                # srcset can hold multiple "url size" entries; take the first url.
                return value.split(",")[0].strip().split(" ")[0]
        return None

    def parse_listing_cards(self, soup: BeautifulSoup, config: SiteConfig) -> list[dict]:
        """Extract (title, url, thumbnail) tuples from a listing page."""
        cards = []
        for card in soup.select(config.card_selector):
            link = card.select_one(config.title_link_selector)
            if link is None or not link.get("href"):
                continue
            title = link.get_text(strip=True)
            url = self._absolute(config.base_url, link["href"])
            image = self._best_image(card.select_one(config.image_selector))
            cards.append({
                "title": title,
                "url": url,
                "image_url": self._absolute(config.base_url, image),
            })
        return cards

    def parse_article(self, soup: BeautifulSoup, config: SiteConfig) -> tuple[str, str | None]:
        """Return (description_text, image_url) from a promo's article page."""
        description = ""
        node = soup.select_one(config.description_selector)
        if node is not None:
            description = node.get_text(separator="\n", strip=True)

        image_url = self._best_image(soup.select_one(config.article_image_selector))
        return description, self._absolute(config.base_url, image_url)

    # -- orchestration -------------------------------------------------
    def iter_promos(self, config: SiteConfig, max_pages: int = 5):
        """Yield :class:`Promo` for every promo found on up to ``max_pages``
        listing pages, fetching each article for its description/image."""
        for page in range(1, max_pages + 1):
            listing_url = config.listing_url.format(page=page)
            soup = self.fetch(listing_url)
            if soup is None:
                break

            cards = self.parse_listing_cards(soup, config)
            if not cards:
                logger.info("No more promos found at %s; stopping.", listing_url)
                break

            for card in cards:
                if not card["url"]:
                    continue
                article_soup = self.fetch(card["url"])
                description, article_image = ("", None)
                if article_soup is not None:
                    description, article_image = self.parse_article(article_soup, config)

                period = parse_date_range(card["title"]) or parse_date_range(description)
                start, end = period if period else (None, None)

                yield Promo(
                    site=config.name,
                    title=card["title"],
                    url=card["url"],
                    image_url=article_image or card["image_url"],
                    description=description,
                    period_start=start,
                    period_end=end,
                )
