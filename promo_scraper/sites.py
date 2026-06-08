"""Per-site configuration for the promo scraper.

Both Giladiskon and Katalogpromosi are WordPress sites that publish one
article per promo, listed on category/archive pages. The CSS selectors
below target the conventional WordPress markup these themes use
(``article`` cards with an ``entry-title`` link and a ``post-thumbnail``
image). If a site changes its theme, only this file needs updating --
adjust the selectors to match the new markup (use your browser's
"inspect element" to find the right classes).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SiteConfig:
    name: str
    base_url: str
    # URL of page N of the listing (1-indexed). Use {page} as placeholder.
    listing_url: str
    # Selectors applied to a listing page to find each promo "card".
    card_selector: str
    # Within a card: the <a> that links to and titles the promo.
    title_link_selector: str
    # Within a card: the <img> used as a thumbnail/preview.
    image_selector: str
    # Within the full article page: where the discount description lives.
    description_selector: str
    # Within the full article page: the main/featured image (fallback to
    # the listing thumbnail when absent).
    article_image_selector: str


SITES: dict[str, SiteConfig] = {
    "giladiskon": SiteConfig(
        name="Giladiskon",
        base_url="https://www.giladiskon.com",
        listing_url="https://www.giladiskon.com/page/{page}",
        card_selector="article",
        title_link_selector="h2.entry-title a, h3.entry-title a, a.entry-title-link",
        image_selector="img",
        description_selector=(
            "div.entry-content, div.entry-summary, "
            "div.post-content, article .content"
        ),
        article_image_selector="div.entry-content img, figure.post-thumbnail img, img.wp-post-image",
    ),
    "katalogpromosi": SiteConfig(
        name="Katalogpromosi",
        base_url="https://katalogpromosi.com",
        listing_url="https://katalogpromosi.com/page/{page}",
        card_selector="article",
        title_link_selector="h2.entry-title a, h3.entry-title a, a.entry-title-link",
        image_selector="img",
        description_selector=(
            "div.entry-content, div.entry-summary, "
            "div.post-content, article .content"
        ),
        article_image_selector="div.entry-content img, figure.post-thumbnail img, img.wp-post-image",
    ),
}


def get_site(key: str) -> SiteConfig:
    try:
        return SITES[key]
    except KeyError as exc:
        valid = ", ".join(sorted(SITES))
        raise ValueError(f"Unknown site '{key}'. Valid options: {valid}") from exc
