# Promo Scraper — Giladiskon & Katalogpromosi

Program Python untuk mengambil daftar promo dari **Giladiskon**
(`giladiskon.com`) dan **Katalogpromosi** (`katalogpromosi.com`), lalu
menyaring promo yang berlaku pada rentang tanggal yang kamu tentukan —
lengkap dengan **keterangan diskon** dan **gambar promo**.

## Instalasi

```bash
pip install -r requirements.txt
```

## Pemakaian

```bash
python main.py --start 2026-06-01 --end 2026-06-30
```

Argumen penting:

| Argumen | Keterangan |
| --- | --- |
| `--start`, `--end` | Rentang tanggal yang dicari, format `YYYY-MM-DD` (wajib) |
| `--site` | `giladiskon`, `katalogpromosi`, atau `all` (default `all`) |
| `--max-pages` | Berapa halaman daftar promo yang dijelajahi per situs (default `5`) |
| `--include-undated` | Sertakan juga promo yang periodenya tidak bisa terbaca dari halaman |
| `--output` | `table` (tampil di terminal, default), `json`, atau `csv` |
| `--output-file` | Simpan hasil `json`/`csv` ke file alih-alih ke layar |
| `--download-images DIR` | Unduh gambar tiap promo yang cocok ke folder `DIR` |
| `-v` | Tampilkan log proses (halaman yang sedang diambil, dll.) |

### Contoh

Tampilkan promo dari kedua situs yang berlaku 1–30 Juni 2026:

```bash
python main.py --start 2026-06-01 --end 2026-06-30
```

Hanya dari Giladiskon, simpan sebagai JSON, dan unduh gambarnya:

```bash
python main.py --start 2026-06-01 --end 2026-06-30 \
  --site giladiskon --output json --output-file promo_juni.json \
  --download-images ./promo_images
```

Setiap entri hasil berisi: situs asal, judul promo, periode (tanggal mulai
& selesai), URL artikel, URL gambar, dan keterangan/deskripsi diskon.

## Cara kerja

1. Membuka halaman daftar promo (`/page/1`, `/page/2`, ...) di tiap situs.
2. Mengambil judul, tautan, dan thumbnail tiap promo dari kartu listingnya.
3. Membuka halaman artikel tiap promo untuk mengambil **deskripsi lengkap**
   dan **gambar utama** (fallback ke thumbnail jika artikel tak punya gambar).
4. Membaca rentang tanggal promo dari judul/teks (mendukung format Indonesia
   seperti `30 April - 13 Mei 2026`, `06-08 Maret 2026`, `1 - 30 Juni 2026`,
   atau tanggal tunggal `8 Juni 2026`).
5. Menyaring promo yang periodenya **beririsan** dengan rentang tanggal
   pilihanmu (`--start`/`--end`), lalu menampilkan/menyimpan hasilnya.

## Menyesuaikan selector situs

Struktur HTML situs (nama class, dsb.) bisa berubah sewaktu-waktu karena
keduanya adalah situs WordPress yang temanya bisa di-update. Semua selector
CSS yang dipakai untuk membaca kartu promo, judul, gambar, dan deskripsi ada
di satu tempat: `promo_scraper/sites.py`. Jika program berhenti menemukan
promo atau salah membaca konten, cek struktur HTML terbaru situs (klik kanan
→ *Inspect*) lalu sesuaikan selector di file tersebut — tidak perlu mengubah
bagian lain dari program.

## Menjalankan tes

Logika parsing tanggal & scraping diuji dengan halaman HTML contoh (fixture)
sehingga bisa diverifikasi tanpa koneksi ke situs aslinya:

```bash
pip install pytest
pytest tests/ -v
```
