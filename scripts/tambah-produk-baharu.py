#!/usr/bin/env python3
"""
Tambah produk pembekal yang belum ada dalam katalog, lengkap dengan gambar.

Sumber : data-mentah/igp-semua.json  (WooCommerce Store API igpremium.com.my)
Sasaran: src/data/produk.json + public/gambar/

Gambar yang dijana bagi setiap produk:
  <slug>.webp          cover 900px
  <slug>-600.webp      cover 600px   (srcset kad)
  <slug>-300.webp      cover 300px   (thumbnail galeri)
  <slug>-gN.webp       galeri 700px  (gambar ke-2 dan seterusnya)
  <slug>-gN-t.webp     galeri 160px  (thumbnail jalur galeri)

Selamat dijalankan berulang: produk yang sudah ada dilangkau, gambar yang
sudah wujud tidak dimuat turun semula.
"""

import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMBER = os.path.join(ROOT, "data-mentah/igp-semua.json")
DATA = os.path.join(ROOT, "src/data/produk.json")
DEST = os.path.join(ROOT, "public/gambar")

COVER = {"": (900, 76), "-600": (600, 76), "-300": (300, 78)}
GALERI = (700, 74)
THUMB = (160, 72)
JEDA = 0.35
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def slugify(s):
    s = html.unescape(s or "").lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")[:70]


def harga_sen(p, kunci="price"):
    v = (p.get("prices") or {}).get(kunci)
    try:
        return round(int(v) / 100, 2)
    except (TypeError, ValueError):
        return None


def muat(url):
    # Sesetengah nama produk ada aksara bukan-ASCII (Ｉ, ², …) dan URL itu
    # mesti di-encode — jika tidak urllib gagal dengan 'ascii' codec error.
    url = urllib.parse.quote(url, safe=":/?&=#%+~@,;!$'()*[]")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def simpan(raw, laluan, maks, kualiti):
    """Buka imej mentah, kecilkan, simpan sebagai WebP."""
    if os.path.exists(laluan):
        return False
    tmp = "/tmp/_img_tambah"
    with open(tmp, "wb") as f:
        f.write(raw)
    im = Image.open(tmp)
    if im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGB")
    im.thumbnail((maks, maks), Image.LANCZOS)
    im.save(laluan, "WEBP", quality=kualiti, method=6)
    return True


def rekod(p):
    """Bina satu rekod produk ikut skema katalog kita."""
    kat = [html.unescape(c["name"]) for c in (p.get("categories") or [])]
    h = harga_sen(p)
    pr = (p.get("prices") or {}).get("price_range")
    r = {
        "id": p["id"],
        "slug": slugify(p.get("name") or str(p["id"])),
        "nama": html.unescape(p.get("name") or ""),
        "sku": p.get("sku") or None,
        "harga": h if h is not None else 0,
        "kategori": kat[0] if kat else "Miscellaneous",
        "kategori_lain": kat[1:],
        "jenama": None,
        "gambar": None,
    }
    if pr and pr.get("min_amount") != pr.get("max_amount"):
        try:
            r["harga"] = round(int(pr["min_amount"]) / 100, 2)
            r["harga_max"] = round(int(pr["max_amount"]) / 100, 2)
        except (TypeError, ValueError):
            pass
    return r


def main():
    sumber = json.load(open(SUMBER, encoding="utf-8"))
    produk = json.load(open(DATA, encoding="utf-8"))
    os.makedirs(DEST, exist_ok=True)

    ada_sku = {(x.get("sku") or "").strip().upper() for x in produk if x.get("sku")}
    ada_id = {x["id"] for x in produk}
    ada_slug = {x["slug"] for x in produk}

    baharu = [p for p in sumber
              if (p.get("sku") or "").strip().upper() not in ada_sku and p["id"] not in ada_id]
    print(f"pembekal {len(sumber)} | katalog {len(produk)} | baharu {len(baharu)}", flush=True)

    ditambah = gagal = 0
    for i, p in enumerate(baharu, 1):
        imgs = p.get("images") or []
        if not imgs:
            gagal += 1
            continue

        r = rekod(p)

        # slug mesti unik
        asas, n = r["slug"], 2
        while r["slug"] in ada_slug:
            r["slug"] = f"{asas}-{n}"
            n += 1

        try:
            # --- cover + varian ---
            raw = muat(imgs[0]["src"])
            for akhiran, (maks, kualiti) in COVER.items():
                simpan(raw, os.path.join(DEST, f"{r['slug']}{akhiran}.webp"), maks, kualiti)
            r["gambar"] = f"/gambar/{r['slug']}.webp"

            # --- galeri (gambar ke-2 ke atas, maksimum 5) ---
            galeri = []
            for j, g in enumerate(imgs[1:6], start=2):
                src = (g.get("src") or "")
                if not src:
                    continue
                graw = muat(src)
                nama = f"{r['slug']}-g{j}"
                simpan(graw, os.path.join(DEST, f"{nama}.webp"), GALERI[0], GALERI[1])
                simpan(graw, os.path.join(DEST, f"{nama}-t.webp"), THUMB[0], THUMB[1])
                galeri.append(f"/gambar/{nama}.webp")
                time.sleep(JEDA)
            if galeri:
                r["galeri"] = galeri

            produk.append(r)
            ada_slug.add(r["slug"])
            ditambah += 1
        except Exception as e:
            gagal += 1
            if gagal <= 8:
                print(f"  ! {r['slug'][:40]}: {str(e)[:70]}", flush=True)

        if i % 25 == 0:
            json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"  {i}/{len(baharu)} — ditambah {ditambah}, gagal {gagal}", flush=True)
        time.sleep(JEDA)

    json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nSELESAI — ditambah {ditambah}, gagal {gagal}", flush=True)
    print(f"jumlah katalog sekarang: {len(produk)}", flush=True)


if __name__ == "__main__":
    main()
