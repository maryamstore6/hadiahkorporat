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
AMBANG_MONTAJ = 0.30   # isi bingkai bawah ini -> guna montaj 2x2


def slugify(s):
    s = html.unescape(s or "").lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:70]


def bbox_kandungan(im):
    rgb = im.convert("RGB")
    beza = ImageChops.difference(rgb, Image.new("RGB", rgb.size, LATAR)).convert("L")
    return beza.point(lambda p: 255 if p > AMBANG else 0).getbbox()


def blob_terbesar(im, saiz=96, ambang=20):
    """
    Nisbah luas blob (bintik bersambung) bukan-putih TERBESAR terhadap imej.

    Kenapa perlu: sesetengah gambar pembekal ialah HELAIAN SPESIFIKASI —
    ada teks, titik warna dan garisan teknikal bersama produk. Bbox-nya besar
    (jadi skor kepenuhan nampak bagus) tetapi produk sebenar kecil dan jubin
    nampak kosong. Gambar produk bersih pula didominasi SATU blob besar.

    Nilai tinggi (0.6-1.0) = produk bersih. Rendah (0.2-0.4) = helaian spes.
    """
    kecil = im.convert("RGB").resize((saiz, saiz), Image.LANCZOS)
    px = kecil.load()
    topeng = [[0] * saiz for _ in range(saiz)]
    for y in range(saiz):
        for x in range(saiz):
            r, g, b = px[x, y]
            if (255 - r) + (255 - g) + (255 - b) > ambang * 3:
                topeng[y][x] = 1
    dilawat = [[False] * saiz for _ in range(saiz)]
    terbaik = 0
    for y in range(saiz):
        for x in range(saiz):
            if topeng[y][x] and not dilawat[y][x]:
                tindih = [(x, y)]
                dilawat[y][x] = True
                luas = 0
                while tindih:
                    cx, cy = tindih.pop()
                    luas += 1
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < saiz and 0 <= ny < saiz
                                and topeng[ny][nx] and not dilawat[ny][nx]):
                            dilawat[ny][nx] = True
                            tindih.append((nx, ny))
                terbaik = max(terbaik, luas)
    return terbaik / (saiz * saiz)


def nilai(im):
    """
    Skor 0..1: gabungan (a) kepenuhan bingkai segi empat dan
    (b) sama ada gambar itu produk bersih atau helaian spesifikasi.
    """
    bb = bbox_kandungan(im)
    if not bb:
        return -1.0
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    if w < 6 or h < 6:
        return -1.0
    s = min(1.0 / w, 1.0 / h)
    isi = (w * s) * (h * s)                       # nisbah segi empat
    res = min(1.0, min(im.size) / RES_MIN)        # hukuman resolusi kecil
    blob = blob_terbesar(im)                      # hukuman helaian spesifikasi
    return isi * res * (0.5 + 0.5 * min(1.0, blob / 0.5))


def sel(im, lebar, tinggi, padding=0.10):
    """Muatkan satu produk ke dalam satu sel tanpa memotongnya."""
    im = im.convert("RGB")
    bb = bbox_kandungan(im)
    if bb:
        im = im.crop(bb)
    maks_w = int(lebar * (1 - 2 * padding))
    maks_h = int(tinggi * (1 - 2 * padding))
    skala = min(maks_w / im.width, maks_h / im.height)
    w = max(1, round(im.width * skala))
    h = max(1, round(im.height * skala))
    kotak = Image.new("RGB", (lebar, tinggi), LATAR)
    salinan = im.resize((w, h), Image.LANCZOS)
    kotak.paste(salinan, ((lebar - w) // 2, (tinggi - h) // 2))
    return kotak


def montaj(imej_senarai, lebar=1200, tinggi=None):
    """
    Susun 2-4 produk dalam grid 2x2.

    Dipakai apabila produk dalam kategori itu semuanya nipis/tinggi —
    satu produk akan meninggalkan bingkai hampir seluruhnya putih, tetapi
    empat produk memenuhkan bingkai dan kelihatan seperti jubin kategori.
    """
    tinggi = tinggi or int(lebar / NISBAH)
    jurang = int(lebar * 0.012)
    kanvas = Image.new("RGB", (lebar, tinggi), LATAR)
    sel_w = (lebar - jurang) // 2
    sel_h = (tinggi - jurang) // 2
    kedudukan = [(0, 0), (sel_w + jurang, 0),
                 (0, sel_h + jurang), (sel_w + jurang, sel_h + jurang)]
    for im, (x, y) in zip(imej_senarai[:4], kedudukan):
        kanvas.paste(sel(im, sel_w, sel_h), (x, y))
    return kanvas


def bbox_blob_terbesar(im, saiz=96, ambang=20):
    """
    Kotak sempadan blob bukan-putih TERBESAR (dalam koordinat imej asal).

    Dipakai sebagai penyelamat untuk kategori yang gambarnya helaian
    spesifikasi: memotong kepada blob terbesar membuang teks/spes di tepi
    dan mengezum masuk ke produk sebenar.
    """
    kecil = im.convert("RGB").resize((saiz, saiz), Image.LANCZOS)
    px = kecil.load()
    topeng = [[0] * saiz for _ in range(saiz)]
    for y in range(saiz):
        for x in range(saiz):
            r, g, b = px[x, y]
            if (255 - r) + (255 - g) + (255 - b) > ambang * 3:
                topeng[y][x] = 1
    dilawat = [[False] * saiz for _ in range(saiz)]
    terbaik, kotak = 0, None
    for y in range(saiz):
        for x in range(saiz):
            if topeng[y][x] and not dilawat[y][x]:
                tindih = [(x, y)]
                dilawat[y][x] = True
                luas = 0
                x0 = x1 = x
                y0 = y1 = y
                while tindih:
                    cx, cy = tindih.pop()
                    luas += 1
                    x0, x1 = min(x0, cx), max(x1, cx)
                    y0, y1 = min(y0, cy), max(y1, cy)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < saiz and 0 <= ny < saiz
                                and topeng[ny][nx] and not dilawat[ny][nx]):
                            dilawat[ny][nx] = True
                            tindih.append((nx, ny))
                if luas > terbaik:
                    terbaik, kotak = luas, (x0, y0, x1 + 1, y1 + 1)
    if not kotak:
        return None
    w, h = im.size
    fx, fy = w / saiz, h / saiz
    return (int(kotak[0] * fx), int(kotak[1] * fy),
            int(kotak[2] * fx), int(kotak[3] * fy))


def jubin_blob(im):
    """Seperti jubin(), tetapi potong kepada blob terbesar dahulu."""
    bb = bbox_blob_terbesar(im)
    kerja = im
    if bb and (bb[2] - bb[0]) > 20 and (bb[3] - bb[1]) > 20:
        kerja = im.crop(bb)
    lebar, tinggi = 1200, int(1200 / NISBAH)
    maks_w = int(lebar * (1 - 2 * PADDING))
    maks_h = int(tinggi * (1 - 2 * PADDING))
    skala = min(maks_w / kerja.width, maks_h / kerja.height)
    w = max(1, round(kerja.width * skala))
    h = max(1, round(kerja.height * skala))
    kanvas = Image.new("RGB", (lebar, tinggi), LATAR)
    kanvas.paste(kerja.convert("RGB").resize((w, h), Image.LANCZOS),
                 ((lebar - w) // 2, (tinggi - h) // 2))
    return kanvas


def putih_peratus(kanvas):
    """Peratus piksel hampir-putih dalam kanvas — ukuran sebenar, bukan jangkaan."""
    kecil = kanvas.copy()
    kecil.thumbnail((200, 200), Image.LANCZOS)
    px = list(kecil.convert("RGB").getdata())
    n = len(px)
    return sum(1 for r, g, b in px if r > 245 and g > 245 and b > 245) / n * 100


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


def ambil_penuh(src, kunci):
    """Muat turun gambar saiz penuh pembekal (cache di /tmp).

    PENTING: `kunci` mesti unik bagi SETIAP PRODUK, bukan setiap kategori.
    Jika cache dikunci ikut kategori, jalaran kedua akan guna semula gambar
    produk lama walaupun calon terbaik sudah bertukar.
    """
    os.makedirs(CACHE, exist_ok=True)
    laluan = os.path.join(CACHE, re.sub(r"[^a-zA-Z0-9_.-]", "_", kunci) + ".img")
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

        def imej_penuh(p):
            s = (igp.get(p["id"], {}).get("images") or [{}])[0].get("src")
            if s:
                return ambil_penuh(s, f"{p['id']}-{slug}")
            return Image.open(os.path.join(ROOT, "public" + p["gambar"]))

        def tulis(kanvas):
            for lebar, kualiti in SAIZ:
                c = kanvas.copy()
                c.thumbnail((lebar, lebar), Image.LANCZOS)
                c.save(os.path.join(KELUAR, f"{slug}-{lebar}.webp"),
                       "WEBP", quality=kualiti, method=6)

        # UKUR HASIL SEBENAR, bukan jangkaan. Skor dari salinan 900px tidak
        # semestinya sama dengan gambar penuh (bbox boleh berbeza), jadi cuba
        # kedua-dua pendekatan dan simpan yang paling penuh.
        calon_kanvas = []

        # (a) satu produk — cuba beberapa calon teratas
        for sc, p in calon[:5]:
            try:
                kanvas_t = jubin(imej_penuh(p))
                calon_kanvas.append((putih_peratus(kanvas_t), "tunggal", p["nama"], kanvas_t))
                time.sleep(0.2)
            except Exception as e:
                print(f"  ~ {slug} ({p['nama'][:24]}): {str(e)[:44]}", flush=True)

        # (b) montaj 2x2 — kalau 4 produk memenuhkan bingkai lebih baik
        imej4 = []
        for sc, p in calon[:4]:
            try:
                imej4.append(imej_penuh(p))
                time.sleep(0.2)
            except Exception:
                continue
        if len(imej4) >= 2:
            try:
                mk = montaj(imej4)
                calon_kanvas.append((putih_peratus(mk), "montaj",
                                     " + ".join(p["nama"][:20] for _, p in calon[:len(imej4)]), mk))
            except Exception as e:
                print(f"  ~ montaj {slug}: {str(e)[:44]}", flush=True)

        if not calon_kanvas:
            gagal += 1
            print(f"  ! {k}: semua calon gagal", flush=True)
            continue

        pp_akhir, jenis, dari, kanvas = min(calon_kanvas, key=lambda x: x[0])

        # Penyelamat: kalau bingkai masih >70% putih, cuba zum ke blob terbesar
        # (membuang teks spesifikasi yang membuatkan produk nampak kecil).
        if pp_akhir > 70:
            for sc, p in calon[:3]:
                try:
                    cuba = jubin_blob(imej_penuh(p))
                    pp2 = putih_peratus(cuba)
                    if pp2 < pp_akhir - 3:
                        pp_akhir, jenis, dari, kanvas = pp2, "blob", p["nama"], cuba
                        break
                except Exception:
                    continue
                time.sleep(0.2)
        tulis(kanvas)
        hasil[k] = {"slug": slug, "jenis": jenis, "dari": dari,
                    "putih": round(pp_akhir, 1)}

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
        jenis = hasil[k].get("jenis", "tunggal")
        if pp > 75:
            print(f"{k[:30]:32s} {pp:6.1f}%  {st:11s} [{jenis}]")
        if pp > 85:
            teruk += 1
    montaj_n = sum(1 for v in hasil.values() if v.get("jenis") == "montaj")
    print(f"\nkategori masih kosong: {teruk} | guna montaj: {montaj_n}")


if __name__ == "__main__":
    main()
