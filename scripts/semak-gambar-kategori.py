#!/usr/bin/env python3
"""
Semakan pantas: pastikan tiada gambar kategori yang 'pecah' (hampir putih).

Jalankan selepas scripts/jana-gambar-kategori.py, dan sebelum deploy.
Keluar dengan kod 1 jika ada kategori yang melebihi ambang, supaya masalah
ini tidak terlepas ke laman secara senyap.

Guna:
    python3 scripts/semak-gambar-kategori.py            # lapor sahaja
    python3 scripts/semak-gambar-kategori.py --ketat 70 # ambang lebih ketat
"""

import glob
import json
import os
import sys

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KELUAR = os.path.join(ROOT, "public/kategori")
AMBANG = 80          # > ini = gagal
WASPADA = 75         # 75-80 = beri amaran


def hitung(laluan):
    im = Image.open(laluan).convert("RGB")
    kecil = im.copy()
    kecil.thumbnail((200, 200), Image.LANCZOS)
    px = list(kecil.getdata())
    n = len(px)
    putih = sum(1 for r, g, b in px if r > 245 and g > 245 and b > 245)
    # saiz kandungan relatif (bbox bukan-putih)
    beza = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L")
    bb = beza.point(lambda p: 255 if p > 10 else 0).getbbox()
    if bb:
        lebar, tinggi = bb[2] - bb[0], bb[3] - bb[1]
        kandungan = (lebar * tinggi) / (im.width * im.height) * 100
    else:
        kandungan = 0
    return putih / n * 100, kandungan


def main():
    ketat = "--ketat" in sys.argv
    ambang = WASPADA if ketat else AMBANG

    if not os.path.isdir(KELUAR):
        print("Folder public/kategori tiada — jalankan jana-gambar-kategori.py dahulu.")
        return 1

    produk = json.load(open(os.path.join(ROOT, "src/data/produk.json"), encoding="utf-8"))
    semua_kat = {p["kategori"] for p in produk}

    indeks = {}
    f_indeks = os.path.join(KELUAR, "_indeks.json")
    if os.path.exists(f_indeks):
        indeks = json.load(open(f_indeks, encoding="utf-8"))

    gagal, waspada, ok, tiada = [], [], 0, []

    for kat in sorted(semua_kat):
        slug = (indeks.get(kat) or {}).get("slug")
        if not slug:
            # slug mungkin berbeza; cuba kesan melalui fail
            tiada.append(kat)
            continue
        f = os.path.join(KELUAR, f"{slug}-400.webp")
        if not os.path.exists(f):
            tiada.append(kat)
            continue
        pp, kand = hitung(f)
        if pp > ambang:
            gagal.append((kat, pp, kand))
        elif pp > WASPADA:
            waspada.append((kat, pp, kand))
        else:
            ok += 1

    print(f"kategori diperiksa : {len(semua_kat)}")
    print(f"  OK              : {ok}")
    print(f"  waspada (>{WASPADA}%) : {len(waspada)}")
    print(f"  GAGAL  (>{ambang}%) : {len(gagal)}")
    print(f"  tiada gambar    : {len(tiada)}")

    for kat, pp, kand in sorted(gagal, key=lambda x: -x[1]):
        print(f"  GAGAL   {kat[:32]:34s} putih {pp:5.1f}%  kandungan {kand:4.1f}%")
    for kat, pp, kand in sorted(waspada, key=lambda x: -x[1]):
        print(f"  waspada {kat[:32]:34s} putih {pp:5.1f}%")
    for kat in tiada:
        print(f"  TIADA   {kat}")

    if gagal or tiada:
        print("\nGAGAL — jana semula dengan: python3 scripts/jana-gambar-kategori.py")
        return 1
    print("\nLULUS — tiada gambar kategori yang pecah.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
