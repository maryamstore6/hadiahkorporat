#!/usr/bin/env python3
"""
Muat turun SEMUA gambar produk, auto-trim bingkai putih, dan optimize.

Kenapa auto-trim: gambar sumber 2500x2500 dengan produk kecil di tengah.
Bila dipaparkan dalam jubin kad 4:3, produk nampak kecil dan kerdil. Selepas
bingkai putih dibuang, produk mengisi bingkai — dan kita boleh guna piksel
LEBIH KECIL untuk saiz paparan yang sama (fail lebih ringan).

Keluaran bagi setiap produk (dalam public/gambar/):
    <slug>.webp        cover 900px   (halaman produk)
    <slug>-600.webp    cover 600px   (tablet / telefon retina)
    <slug>-300.webp    cover 300px   (kad katalog telefon)
    <slug>-g2.webp     galeri 700px  (imej ke-2)
    <slug>-g2-t.webp   galeri 160px  (thumbnail)
    ... g3, g4 ...      sehingga 4 imej tambahan

Sopan pada pelayan sumber: satu permintaan pada satu masa, jeda 0.35s.
Boleh disambung semula: fail yang sudah wujud dilangkau.
"""

import json
import os
import sys
import time
import urllib.request

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMBER = "/tmp/igp_products.json"
DATA = os.path.join(ROOT, "src/data/produk.json")
DEST = os.path.join(ROOT, "public/gambar")
TMP = "/tmp/_img_dl"

COVER = [(900, 82), (600, 80), (300, 78)]
GALERI = (700, 78)
THUMB = (160, 72)
MAKS_GALERI = 3          # imej tambahan (selain cover)
JEDA = 0.35
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/156.0 Safari/537.36"


def trim(im, toleransi=20, padding=0.02):
    """Buang latar sekeliling produk. Latar dikesan dari 4 sudut."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    sudut = [rgb.getpixel(p) for p in [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]]
    latar = tuple(sum(c[i] for c in sudut) // 4 for i in range(3))
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, latar)).convert("L")
    kotak = diff.point(lambda v: 255 if v > toleransi else 0).getbbox()
    if not kotak:
        return rgb
    l, t, r, b = kotak
    # kalau "kandungan" meliputi hampir seluruh gambar, jangan potong
    if (r - l) > w * 0.985 and (b - t) > h * 0.985:
        return rgb
    px = int(max(r - l, b - t) * padding)
    return rgb.crop((max(0, l - px), max(0, t - px), min(w, r + px), min(h, b + px)))


def simpan(im, laluan, maks, kualiti):
    salinan = im.copy()
    if salinan.width > maks or salinan.height > maks:
        salinan.thumbnail((maks, maks), Image.LANCZOS)
    salinan.save(laluan, "WEBP", quality=kualiti, method=6)


def muat_turun(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def main():
    sumber = {p["id"]: p for p in json.load(open(SUMBER, encoding="utf-8"))}
    produk = json.load(open(DATA, encoding="utf-8"))
    os.makedirs(DEST, exist_ok=True)

    ada_imej = [p for p in produk if (sumber.get(p["id"], {}).get("images") or [])]
    print(f"produk: {len(produk)} | ada imej: {len(ada_imej)}", flush=True)

    ok_cover = ok_galeri = gagal = dilangkau = 0

    for i, p in enumerate(produk, 1):
        imgs = [x["src"] for x in (sumber.get(p["id"], {}).get("images") or []) if x.get("src")]
        if not imgs:
            continue

        slug = p["slug"]
        sudah = os.path.exists(os.path.join(DEST, f"{slug}.webp"))

        # ---- Cover ----
        if not sudah:
            try:
                open(TMP, "wb").write(muat_turun(imgs[0]))
                im = trim(Image.open(TMP))
                simpan(im, os.path.join(DEST, f"{slug}.webp"), *COVER[0])
                simpan(im, os.path.join(DEST, f"{slug}-600.webp"), *COVER[1])
                simpan(im, os.path.join(DEST, f"{slug}-300.webp"), *COVER[2])
                p["gambar"] = f"/gambar/{slug}.webp"
                ok_cover += 1
            except Exception as e:
                gagal += 1
                if gagal <= 6:
                    print(f"  ! cover {slug[:38]}: {str(e)[:60]}", flush=True)
            time.sleep(JEDA)
        else:
            dilangkau += 1
            p.setdefault("gambar", f"/gambar/{slug}.webp")

        # ---- Galeri ----
        galeri = []
        for j, url in enumerate(imgs[1:1 + MAKS_GALERI], start=2):
            keluar = os.path.join(DEST, f"{slug}-g{j}.webp")
            if os.path.exists(keluar):
                galeri.append(f"/gambar/{slug}-g{j}.webp")
                continue
            try:
                open(TMP, "wb").write(muat_turun(url))
                im = trim(Image.open(TMP))
                simpan(im, keluar, *GALERI)
                simpan(im, os.path.join(DEST, f"{slug}-g{j}-t.webp"), *THUMB)
                galeri.append(f"/gambar/{slug}-g{j}.webp")
                ok_galeri += 1
            except Exception:
                gagal += 1
            time.sleep(JEDA)
        if galeri:
            p["galeri"] = galeri

        if i % 40 == 0:
            print(f"  {i}/{len(produk)} — cover {ok_cover}, galeri {ok_galeri}, gagal {gagal}", flush=True)
            json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    fail = [f for f in os.listdir(DEST) if f.endswith(".webp")]
    saiz = sum(os.path.getsize(os.path.join(DEST, f)) for f in fail)
    print(f"\nSELESAI — cover {ok_cover}, galeri {ok_galeri}, gagal {gagal}, dilangkau {dilangkau}", flush=True)
    print(f"jumlah fail: {len(fail)} | saiz folder: {saiz/1024/1024:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
