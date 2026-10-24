#!/usr/bin/env python3
"""
Jana gambar wakil (cover) untuk setiap kategori.

Sumber: gambar cover produk pertama yang ada gambar dalam kategori itu.
Keluaran: public/kategori/<slug>-400.webp dan <slug>-800.webp

Setiap jubin ialah kanvas 4:3 berlatar krim dengan produk di tengah, supaya
semua kategori kelihatan seragam walaupun bentuk produk berbeza (pen tinggi,
beg lebar, dsb) — bukan crop paksa yang memotong produk.
"""

import json
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "src/data/produk.json")
GAMBAR = os.path.join(ROOT, "public/gambar")
KELUAR = os.path.join(ROOT, "public/kategori")

# Jubin SEGI EMPAT: produk menegak (botol, pen) mengisi bingkai jauh lebih baik
# berbanding 4:3, dan ia sepadan dengan bentuk kad produk.
NISBAH = 1.0
# Latar PUTIH: gambar produk pembekal semuanya berlatar putih, jadi jubin putih
# menjadikannya sebati. Latar batu menghasilkan kesan "gambar dalam gambar" —
# nampak jelas pada produk botol/trophy.
LATAR = (255, 255, 255)
PADDING = 0.04
SAIZ = [(800, 80), (400, 78)]


def slugify(s):
    s = s.lower().replace("&amp;", "and").replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:70]


def jubin(im):
    """Letak produk di tengah kanvas 4:3 tanpa memotongnya."""
    lebar = 1200
    tinggi = int(lebar / NISBAH)
    kanvas = Image.new("RGB", (lebar, tinggi), LATAR)

    maks_w = int(lebar * (1 - 2 * PADDING))
    maks_h = int(tinggi * (1 - 2 * PADDING))
    salinan = im.copy()
    salinan.thumbnail((maks_w, maks_h), Image.LANCZOS)

    x = (lebar - salinan.width) // 2
    y = (tinggi - salinan.height) // 2

    if salinan.mode in ("RGBA", "LA", "P"):
        salinan = salinan.convert("RGBA")
        kanvas = kanvas.convert("RGBA")
        kanvas.paste(salinan, (x, y), salinan)
        kanvas = kanvas.convert("RGB")
    else:
        kanvas.paste(salinan.convert("RGB"), (x, y))
    return kanvas


def main():
    os.makedirs(KELUAR, exist_ok=True)
    produk = json.load(open(DATA, encoding="utf-8"))

    # calon pertama setiap kategori
    calon = {}
    for p in produk:
        k = p["kategori"]
        if k in calon:
            continue
        g = p.get("gambar")
        if g and os.path.exists(os.path.join(ROOT, "public" + g)):
            calon[k] = p

    print(f"kategori: {len(set(p['kategori'] for p in produk))} | ada calon: {len(calon)}", flush=True)

    berjaya = gagal = 0
    hasil = {}
    for k, p in sorted(calon.items()):
        slug = slugify(k)
        try:
            im = Image.open(os.path.join(ROOT, "public" + p["gambar"]))
            kanvas = jubin(im)
            for lebar, kualiti in SAIZ:
                s = kanvas.copy()
                s.thumbnail((lebar, lebar), Image.LANCZOS)
                s.save(os.path.join(KELUAR, f"{slug}-{lebar}.webp"), "WEBP", quality=kualiti, method=6)
            hasil[k] = {"slug": slug, "dari": p["nama"]}
            berjaya += 1
        except Exception as e:
            gagal += 1
            print(f"  ! {k}: {str(e)[:70]}")

    json.dump(hasil, open(os.path.join(KELUAR, "_indeks.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    fail = [f for f in os.listdir(KELUAR) if f.endswith(".webp")]
    saiz = sum(os.path.getsize(os.path.join(KELUAR, f)) for f in fail)
    print(f"\nSELESAI — {berjaya} kategori, gagal {gagal}")
    print(f"fail: {len(fail)} | saiz: {saiz/1024:.0f} KB")


if __name__ == "__main__":
    main()
