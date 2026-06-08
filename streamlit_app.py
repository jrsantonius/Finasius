"""Dashboard Streamlit untuk mencari promo Giladiskon & Katalogpromosi
berdasarkan rentang tanggal, lengkap dengan keterangan diskon dan gambar.

Jalankan dengan:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from promo_scraper.cli import _matches_range
from promo_scraper.scraper import Promo, PromoScraper
from promo_scraper.sites import SITES, get_site

st.set_page_config(page_title="Cari Promo - Giladiskon & Katalogpromosi", page_icon="🛍️", layout="wide")


@st.cache_data(show_spinner=False, ttl=60 * 30)
def fetch_promos(site_keys: tuple[str, ...], max_pages: int) -> list[dict]:
    """Scrape & cache raw promos (as dicts, so the result is hashable/cacheable)."""
    scraper = PromoScraper()
    promos: list[Promo] = []
    for key in site_keys:
        config = get_site(key)
        promos.extend(scraper.iter_promos(config, max_pages=max_pages))
    return [p.to_dict() for p in promos]


def _to_promo(data: dict) -> Promo:
    return Promo(
        site=data["site"],
        title=data["title"],
        url=data["url"],
        image_url=data["image_url"],
        description=data["description"],
        period_start=date.fromisoformat(data["period_start"]) if data["period_start"] else None,
        period_end=date.fromisoformat(data["period_end"]) if data["period_end"] else None,
    )


def _format_period(promo: Promo) -> str:
    if not (promo.period_start and promo.period_end):
        return "Periode tidak diketahui"
    if promo.period_start == promo.period_end:
        return promo.period_start.strftime("%d %b %Y")
    return f"{promo.period_start.strftime('%d %b %Y')} – {promo.period_end.strftime('%d %b %Y')}"


def render_promo_card(promo: Promo) -> None:
    with st.container(border=True):
        cols = st.columns([1, 2])
        with cols[0]:
            if promo.image_url:
                st.image(promo.image_url, use_container_width=True)
            else:
                st.write("_(tidak ada gambar)_")
        with cols[1]:
            st.markdown(f"**{promo.title}**")
            st.caption(f"{promo.site} · 🗓️ {_format_period(promo)}")
            description = promo.description.strip()
            if len(description) > 500:
                description = description[:500].rstrip() + "…"
            st.write(description or "_(tidak ada deskripsi)_")
            st.markdown(f"[Lihat selengkapnya]({promo.url})")


def main() -> None:
    st.title("🛍️ Cari Promo: Giladiskon & Katalogpromosi")
    st.write(
        "Pilih rentang tanggal untuk melihat promo yang berlaku pada periode "
        "tersebut, lengkap dengan keterangan diskon dan gambarnya."
    )

    with st.sidebar:
        st.header("Filter")
        today = date.today()
        start = st.date_input("Dari tanggal", value=today, format="DD/MM/YYYY")
        end = st.date_input("Sampai tanggal", value=today + timedelta(days=30), format="DD/MM/YYYY")

        site_labels = {key: cfg.name for key, cfg in SITES.items()}
        selected_labels = st.multiselect(
            "Situs",
            options=list(site_labels.values()),
            default=list(site_labels.values()),
        )
        site_keys = tuple(key for key, label in site_labels.items() if label in selected_labels)

        max_pages = st.slider("Jumlah halaman yang dijelajahi per situs", 1, 10, 5)
        include_undated = st.checkbox(
            "Sertakan promo yang periodenya tidak terbaca", value=False
        )
        search = st.button("🔍 Cari Promo", type="primary", use_container_width=True)

    if not site_keys:
        st.info("Pilih minimal satu situs di sidebar untuk mulai mencari.")
        return

    if start > end:
        st.error("Tanggal awal tidak boleh lebih besar dari tanggal akhir.")
        return

    if not search and "promo_results" not in st.session_state:
        st.info("Atur filter di sidebar lalu klik **Cari Promo** untuk menampilkan hasil.")
        return

    if search:
        with st.spinner("Mengambil data promo... ini bisa memakan waktu beberapa menit."):
            try:
                raw = fetch_promos(site_keys, max_pages)
            except Exception as exc:  # noqa: BLE001 - surfaced to the user
                st.error(f"Gagal mengambil data promo: {exc}")
                return
        st.session_state["promo_results"] = raw
        st.session_state["promo_filter"] = (start, end, include_undated)

    raw = st.session_state.get("promo_results", [])
    promos = [_to_promo(d) for d in raw]
    matched = [p for p in promos if _matches_range(p, start, end, include_undated)]
    matched.sort(key=lambda p: (p.period_start or date.max, p.site))

    st.subheader(f"Hasil: {len(matched)} promo ({start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')})")
    if not matched:
        st.warning("Tidak ada promo yang ditemukan pada rentang tanggal ini.")
        return

    for promo in matched:
        render_promo_card(promo)


if __name__ == "__main__":
    main()
