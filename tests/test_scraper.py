import os
from datetime import date

from promo_scraper.scraper import PromoScraper
from promo_scraper.sites import SiteConfig

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

TEST_SITE = SiteConfig(
    name="TestSite",
    base_url="https://example.test",
    listing_url="https://example.test/page/{page}",
    card_selector="article",
    title_link_selector="h2.entry-title a",
    image_selector="img",
    description_selector="div.entry-content",
    article_image_selector="div.entry-content img, figure.post-thumbnail img, img.wp-post-image",
)


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


class FakeSession:
    """Serves fixture HTML for known URLs and an empty page-2 listing."""

    ROUTES = {
        "https://example.test/page/1": "listing.html",
        "https://example.test/deals/promo-indomaret-30-april-13-mei-2026": "article_indomaret.html",
        "https://example.test/deals/promo-superindo-8-11-juni-2026": "article_superindo.html",
        "https://example.test/deals/promo-kfc-spesial": "article_kfc.html",
    }

    def __init__(self):
        self.headers = {}

    def get(self, url, timeout=None):
        filename = self.ROUTES.get(url)
        if filename is None:
            return FakeResponse("<html><body></body></html>")
        with open(os.path.join(FIXTURES, filename), encoding="utf-8") as fh:
            return FakeResponse(fh.read())


def make_scraper():
    return PromoScraper(session=FakeSession())


def test_iter_promos_extracts_title_period_image_description():
    scraper = make_scraper()
    promos = list(scraper.iter_promos(TEST_SITE, max_pages=2))

    assert len(promos) == 3

    indomaret = next(p for p in promos if "Indomaret" in p.title)
    assert indomaret.period_start == date(2026, 4, 30)
    assert indomaret.period_end == date(2026, 5, 13)
    assert indomaret.image_url == "https://example.test/wp-content/uploads/indomaret-full.jpg"
    assert "diskon hingga 50%" in indomaret.description

    superindo = next(p for p in promos if "Superindo" in p.title)
    assert superindo.period_start == date(2026, 6, 8)
    assert superindo.period_end == date(2026, 6, 11)

    kfc = next(p for p in promos if "KFC" in p.title)
    # No parsable period in either the title or the article body.
    assert kfc.period_start is None and kfc.period_end is None
    assert kfc.image_url == "https://example.test/wp-content/uploads/kfc-full.jpg"


def test_image_falls_back_to_listing_thumbnail_when_article_has_none():
    scraper = make_scraper()

    class NoArticleImageSite(SiteConfig):
        pass

    config = SiteConfig(
        name="TestSite",
        base_url="https://example.test",
        listing_url="https://example.test/page/{page}",
        card_selector="article",
        title_link_selector="h2.entry-title a",
        image_selector="img",
        description_selector="div.entry-content",
        article_image_selector="img.does-not-exist",
    )
    promos = list(scraper.iter_promos(config, max_pages=1))
    indomaret = next(p for p in promos if "Indomaret" in p.title)
    assert indomaret.image_url == "https://example.test/wp-content/uploads/indomaret-thumb.jpg"
