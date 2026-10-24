#!/usr/bin/env python3
"""
Jana gambar wakil (cover) untuk setiap kategori — versi 2.

DUA PEPIJAT DALAM VERSI ASAL:
 1. Ia ambil produk PERTAMA dalam kategori. Kalau produk itu nipis/tinggi
    (pen, lanyard), bingkai jadi hampir seluruhnya putih -> jubin nampak
    kosong/pecah.
 2. PIL `thumbnail()` HANYA mengecil, tidak pernah membesarkan. Jadi imej
    kecil kekal kecil di tengah kanvas putih (lanyard: produk 50px dalam
    kanvas 400px = 98% putih).

PENYELESAIAN:
 - Nilai SEMUA produk dalam kategori; pilih yang gambarannya paling
   memenuhi bingkai segi empat sama (dan resolusinya cukup).
 - Muat turun gambar SAIZ PENUH pembekal (selalunya 2500px) untuk produk
   terpilih — bukan salinan 900px kita.
 - Potong margin putih, kemudian `resize()` supaya produk mengisi bingkai.

Keluaran: public/kategori/<slug>-400.webp dan <slug>-800.webp
"""

import html
import json
import os
import re
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "src/data/produk.json")
SUMBER = os.path.join(ROOT, "data-mentah/igp-semua.json")
KELUAR = os.path.join(ROOT, "public/kategori")
CACHE = "/tmp/kategori-penuh"

NISBAH = 1.0
LATAR = (255, 255, 255)
PADDING = 0.05
SAIZ = [(800, 80), (400, 78)]
AMBANG = 10
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
RES_MIN = 600          # bawah ini, skor dihukum


def slugify(s):
    s = html.unescape(s or "").lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:70]


def bbox_kandungan(im):
    rgb = im.convert("RGB")
    beza = ImageChops.difference(rgb, Image.new("RGB", rgb.size, LATAR)).convert("L")
    return beza.point(lambda p: 255 if p > AMBANG else 0).getbbox()


def nilai(im):
    """Skor 0..1 berapa penuh bingkai segi empat sama akan diisi."""
    bb = bbox_kandungan(im)
    if not bb:
        return -1.0
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    if w < 6 or h < 6:
        return -1.0
    s = min(1.0 / w, 1.0 / h)
    isi = (w * s) * (h * s)                       # nisbah segi empat
    res = min(1.0, min(im.size) / RES_MIN)        # hukuman resolusi kecil
    return isi * res


def jubin(im):
    """Potong margin putih, kemudian BESARKAN supaya mengisi bingkai."""
    im = im.convert("RGB")
    bb = bbox_kandungan(im)
    if bb:
        im = im.crop(bb)

    lebar, tinggi = 1200, int(1200 / NISBAH)
    maks_w = int(lebar * (1 - 2 * PADDING))
    maks_h = int(tinggi * (1 - 2 * PADDING))

    skala = min(maks_w / im.width, maks_h / im.height)
    w = max(1, round(im.width * skala))
    h = max(1, round(im.height * skala))
    salinan = im.resize((w, h), Image.LANCZOS)

    kanvas = Image.new("RGB", (lebar, tinggi), LATAR)
    kanvas.paste(salinan, ((lebar - w) // 2, (tinggi - h) // 2))
    return kanvas


def ambil_penuh(src, slug):
    """Muat turun gambar saiz penuh pembekal (cache di /tmp)."""
    os.makedirs(CACHE, exist_ok=True)
    laluan = os.path.join(CACHE, slug + ".img")
    if os.path.exists(laluan) and os.path.getsize(laluan) > 0:
        try:
            return Image.open(laluan)
        except Exception:
            pass
    url = urllib.parse.quote(src, safe=":/?&=#%+~@,;!$'()*[]")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    if not raw:
        raise ValueError("fail kosong")
    with open(laluan, "wb") as f:
        f.write(raw)
    return Image.open(laluan)


def main():
    os.makedirs(KELUAR, exist_ok=True)
    produk = json.load(open(DATA, encoding="utf-8"))
    igp = {p["id"]: p for p in json.load(open(SUMBER, encoding="utf-8"))}

    ikut_kat = {}
    for p in produk:
        ikut_kat.setdefault(p["kategori"], []).append(p)

    print(f"{len(produk)} produk | {len(ikut_kat)} kategori", flush=True)

    hasil, gagal = {}, 0
    for k, senarai in sorted(ikut_kat.items()):
        calon = []
        for p in senarai:
            g = p.get("gambar")
            if not g:
                continue
            lp = os.path.join(ROOT, "public" + g)
            if not os.path.exists(lp):
                continue
            try:
                im = Image.open(lp)
                sc = nilai(im)
            except Exception:
                continue
            if sc > 0:
                calon.append((sc, p))

        if not calon:
            gagal += 1
            print(f"  ! {k}: tiada calon", flush=True)
            continue

        calon.sort(key=lambda x: -x[0])
        slug = slugify(k)

        def cuba(p):
            s = (igp.get(p["id"], {}).get("images") or [{}])[0].get("src")
            im = ambil_penuh(s, slug) if s else Image.open(os.path.join(ROOT, "public" + p["gambar"]))
            kanvas = jubin(im)
            for lebar, kualiti in SAIZ:
                c = kanvas.copy()
                c.thumbnail((lebar, lebar), Image.LANCZOS)
                c.save(os.path.join(KELUAR, f"{slug}-{lebar}.webp"),
                       "WEBP", quality=kualiti, method=6)
            return True

        berjaya = False
        for sc, p in calon[:4]:            # cuba 4 terbaik sehingga satu berjaya
            try:
                cuba(p)
                hasil[k] = {"slug": slug, "dari": p["nama"], "skor": round(sc, 2)}
                berjaya = True
                break
            except Exception as e:
                print(f"  ~ {slug} ({p['nama'][:28]}): {str(e)[:50]}", flush=True)
                time.sleep(0.3)

        if not berjaya:
            gagal += 1

    json.dump(hasil, open(os.path.join(KELUAR, "_indeks.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # laporkan hasil sebenar
    print(f"\nSELESAI — {len(hasil)} kategori, gagal {gagal}\n", flush=True)
    print(f"{'kategori':32s} {'putih%':>7s}  status")
    teruk = 0
    for k in sorted(hasil):
        f = os.path.join(KELUAR, f"{hasil[k]['slug']}-400.webp")
        im = Image.open(f).convert("RGB")
        px = list(im.getdata())
        pp = sum(1 for r, g, b in px if r > 245 and g > 245 and b > 245) / len(px) * 100
        st = "OK" if pp <= 75 else ("agak putih" if pp <= 85 else "KOSONG")
        if pp > 85:
            teruk += 1
            print(f"{k[:30]:32s} {pp:6.1f}%  {st}")
    print(f"\nkategori masih kosong: {teruk}")


if __name__ == "__main__":
    main()
