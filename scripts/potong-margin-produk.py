#!/usr/bin/env python3
"""
Potong margin putih berlebihan pada gambar produk.

MASALAH: gambar pembekal selalunya kanvas besar dengan produk kecil di tengah
(contoh: pen 636x900 tetapi produk hanya 36x516 = 3.2% daripada imej). Kad
produk guna object-fit: contain, jadi seluruh imej dikecilkan supaya muat —
termasuk margin putihnya — dan produk jadi halus.

PENYELESAIAN: potong kepada kotak sempadan produk (dengan sedikit jidar
keselamatan), jadi produk mengisi bingkai. Kenaikan saiz paparan ~1.7x.

Selamat:
  - imej yang sudah padat (>80% kandungan) tidak disentuh
  - jidar 3% supaya tepi produk tidak terpotong
  - kotak sempadan mesti munasabah (bukan bintik hingar)
  - salinan asal disimpan sekali di public/gambar-asal/ sebelum diubah

Guna:
    python3 scripts/potong-margin-produk.py            # kering (lapor sahaja)
    python3 scripts/potong-margin-produk.py --jalankan # tulis perubahan
"""

import json
import os
import shutil
import sys

from PIL import Image, ImageChops

ROOT = "/home/ubuntu/hadiahkorporat"
GAMBAR = f"{ROOT}/public/gambar"
SIMPAN = f"{ROOT}/public/gambar-asal"
DATA = f"{ROOT}/src/data/produk.json"

AMBANG = 12           # beza piksel untuk dianggap kandungan
PADAT = 0.80          # kandungan > ini -> tidak perlu potong
JIDAR = 0.03          # 3% jidar keselamatan
SAIZ_MAKS = 900


def bbox(im):
    beza = ImageChops.difference(im.convert("RGB"),
                                 Image.new("RGB", im.size, (255, 255, 255))).convert("L")
    return beza.point(lambda v: 255 if v > AMBANG else 0).getbbox()


def potong(laluan, jalankan, salinan_asal=False):
    """Pulangkan (tindakan, butiran)."""
    if not os.path.exists(laluan):
        return "tiada_fail", ""

    im = Image.open(laluan)
    im.load()
    asal = im.size
    if asal[0] < 8 or asal[1] < 8:
        return "terlalu_kecil", f"{asal}"

    bb = bbox(im)
    if not bb:
        return "kosong", f"{asal}"

    w, h = bb[2] - bb[0], bb[3] - bb[1]
    padat = (w * h) / (asal[0] * asal[1])

    # bintik hingar: kotak sangat kecil berbanding imej -> abaikan
    if w < 12 or h < 12:
        return "bintik_hingar", f"bbox={w}x{h}"

    if padat >= PADAT:
        return "sudah_padat", f"{padat*100:.0f}%"

    # jidar keselamatan
    jw = int(w * JIDAR) + 2
    jh = int(h * JIDAR) + 2
    kotak = (max(0, bb[0] - jw), max(0, bb[1] - jh),
             min(asal[0], bb[2] + jw), min(asal[1], bb[3] + jh))

    if not jalankan:
        return "akan_potong", f"{asal[0]}x{asal[1]} -> {kotak[2]-kotak[0]}x{kotak[3]-kotak[1]} (padat {padat*100:.0f}% -> 100%)"

    if salinan_asal:
        os.makedirs(SIMPAN, exist_ok=True)
        simpan = os.path.join(SIMPAN, os.path.basename(laluan))
        if not os.path.exists(simpan):
            shutil.copy2(laluan, simpan)

    baharu = im.convert("RGB").crop(kotak)
    if max(baharu.size) > SAIZ_MAKS:
        baharu.thumbnail((SAIZ_MAKS, SAIZ_MAKS), Image.LANCZOS)
    kualiti = 82 if os.path.basename(laluan).endswith("-t.webp") else 78
    baharu.save(laluan, "WEBP", quality=kualiti, method=6)
    return "dipotong", f"{asal[0]}x{asal[1]} -> {baharu.width}x{baharu.height}"


def main():
    jalankan = "--jalankan" in sys.argv
    produk = json.load(open(DATA, encoding="utf-8"))

    kira = {}
    contoh = []
    for p in produk:
        g = p.get("gambar")
        if not g:
            continue
        f = f"{ROOT}/public{g}"
        tindakan, butiran = potong(f, jalankan, salinan_asal=True)
        kira[tindakan] = kira.get(tindakan, 0) + 1
        if tindakan in ("akan_potong", "dipotong") and len(contoh) < 12:
            contoh.append((p["nama"], butiran))

        # varian -600 / -300 dibina semula dari cover yang sudah dipotong
        if jalankan and tindakan == "dipotong":
            im = Image.open(f)
            for akhiran, maks in (("-600", 600), ("-300", 300)):
                v = im.copy()
                v.thumbnail((maks, maks), Image.LANCZOS)
                v.save(f.replace(".webp", f"{akhiran}.webp"), "WEBP", quality=78, method=6)

    print(("JALANKAN" if jalankan else "KERING (lapor sahaja)") + " — gambar cover produk")
    for k, n in sorted(kira.items(), key=lambda x: -x[1]):
        print(f"  {k:16s} {n}")
    if contoh:
        print("\ncontoh:")
        for nama, butiran in contoh:
            print(f"  {nama[:40]:42s} {butiran}")

    # galeri
    kira_g = {}
    contoh_g = []
    for p in produk:
        for g in (p.get("galeri") or []):
            f = f"{ROOT}/public{g}"
            tindakan, butiran = potong(f, jalankan, salinan_asal=True)
            kira_g[tindakan] = kira_g.get(tindakan, 0) + 1
            if tindakan in ("akan_potong", "dipotong") and len(contoh_g) < 5:
                contoh_g.append((g.split("/")[-1], butiran))
            if jalankan and tindakan == "dipotong":
                im = Image.open(f)
                v = im.copy()
                v.thumbnail((160, 160), Image.LANCZOS)
                v.save(f.replace(".webp", "-t.webp"), "WEBP", quality=72, method=6)

    print("\ngambar galeri:")
    for k, n in sorted(kira_g.items(), key=lambda x: -x[1]):
        print(f"  {k:16s} {n}")
    for nama, butiran in contoh_g:
        print(f"  {nama[:44]:46s} {butiran}")


if __name__ == "__main__":
    main()
