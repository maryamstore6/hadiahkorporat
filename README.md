# HadiahKorporat

Katalog hadiah korporat bercetak logo — **1,296 produk**, 52 kategori.
Dibina dengan **Astro 5** (statik, tiada runtime JS selain penapis katalog).

**Laman live:** https://maryamstore6.github.io/hadiahkorporat/

---

## Apa yang ada

| Halaman | Laluan |
|---|---|
| Utama | `/` |
| Katalog (cari + tapis + susun) | `/katalog` |
| Kategori | `/kategori` · `/kategori/<slug>` |
| Halaman produk (969) | `/produk/<slug>` |
| Cara pesan + FAQ | `/cara-pesan` |
| Minta sebut harga | `/sebut-harga` |
| Hubungi | `/hubungi` |

**Ciri utama**

- **Senarai Sebut Harga** — tambah produk dari mana-mana halaman, disimpan dalam
  `localStorage`, dihantar sebagai satu mesej WhatsApp. Ini pembeza utama berbanding
  kedai yang hanya ada "tambah ke troli".
- **Penapis katalog** — cari nama/kod, tapis ikut kategori dan julat harga, susun ikut harga.
- **Kalkulator bajet** — bilangan × harga seunit, terus di halaman utama.
- **Tiada rangka kerja CSS** — satu fail CSS buatan sendiri, ~16 KB.

---

## Struktur

```
src/
  data/produk.json        ← 1,296 produk (nama, slug, sku, harga, kategori, jenama)
  lib/site.js             ← tetapan laman + pembantu (warna, slug, format harga)
  layouts/Base.astro      ← kepala, kaki, panel senarai sebut harga
  components/ProductCard.astro
  pages/
    index.astro
    katalog.astro
    kategori/index.astro  kategori/[slug].astro
    produk/[slug].astro
    cara-pesan.astro  sebut-harga.astro  hubungi.astro  404.astro
  styles/global.css
```

---

## Jalankan tempatan

```bash
npm install
npm run dev        # http://localhost:4321/hadiahkorporat/
npm run build      # keluaran ke dist/
```

---

## ⚠️ Sebelum guna sebenar — 3 benda WAJIB ditukar

Semua dalam `src/lib/site.js`:

| Tetapan | Sekarang | Tukar kepada |
|---|---|---|
| `nama` | `HadiahKorporat` | Nama jenama sebenar anda |
| `whatsapp` | `60176055349` | Nombor WhatsApp bisnes anda |
| `emel` | `hello@hadiahkorporat.my` | E-mel bisnes anda |

### ⚠️ Ulasan pelanggan masih CONTOH

`src/data/ulasan.json` mengandungi 6 ulasan **bertanda `"contoh": true`** —
nama dan butiran pesanan adalah rekaan untuk mengisi reka bentuk.

**Ganti dengan ulasan sebenar sebelum promosi serius.** Ulasan rekaan boleh
menyalahi undang-undang perlindungan pengguna dan lebih merosakkan
kredibiliti daripada tiada ulasan langsung.

Bentuk setiap rekod:

```json
{
  "nama": "Nama Pelanggan",
  "bintang": 5,
  "teks": "Petikan ulasan sebenar...",
  "bulan": "Ogos 2026",
  "pesanan": "120 pcs mug",
  "acara": "sukan tahunan"
}
```

Buang `"contoh": true` apabila sudah guna data sebenar.

**Gambar produk:** ketika ini setiap kad memaparkan jubin berwarna dengan inisial
(sebagai pengganti). Untuk guna gambar sebenar:

1. Letak fail gambar dalam `public/gambar/` (cth. `public/gambar/pen-phylex.jpg`)
2. Dalam `src/data/produk.json`, tambah medan `"gambar": "/gambar/pen-phylex.jpg"`
3. Dalam `src/components/ProductCard.astro`, ganti `<span class="ph">` dengan `<img>`

**Jangan guna gambar dari laman lain** — ia hak cipta pemiliknya. Ambil gambar
sendiri atau minta daripada pembekal anda.

---

## Harga

Semua harga dalam `produk.json` ialah **harga seunit asas** (RM), diambil daripada
senarai awam pembekal. Ia belum termasuk kos cetakan logo dan penghantaran — nota ini
sudah dipaparkan pada setiap halaman produk.

---

## Deploy

- **Sumber** → cabang `main`
- **Laman bina** → cabang `gh-pages` (kandungan `dist/`)

Selepas `npm run build`:

```bash
npx gh-pages -d dist      # atau salin dist/ ke cabang gh-pages secara manual
```

GitHub Pages dihidupkan dari cabang `gh-pages`, folder `/` (root).
Fail `.nojekyll` mesti ada supaya folder `_astro/` tidak diabaikan.
