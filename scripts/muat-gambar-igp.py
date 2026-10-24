#!/usr/bin/env python3
"""
Muat turun gambar produk dan hos sendiri (JANGAN hotlink ke pelayan asal).

- Muat turun gambar UTAMA setiap produk
- Optimize: maks 900px, WebP kualiti 82
- Simpan ke public/gambar/<slug>.webp
- Tulis medan "gambar" dalam src/data/produk.json

Sopan terhadap pelayan sumber: 1 permintaan pada satu masa + jeda 0.4s.
Menyambung semula: produk yang sudah ada gambar dilangkau.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMBER = "/tmp/igp_products.json"
DATA = os.path.join(ROOT, "src/data/produk.json")
DEST = os.path.join(ROOT, "public/gambar")
MAKS = 900
KUALITI = 82
JEDA = 0.4
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/156.0 Safari/537.36"

from PIL import Image


def main():
    sumber = {p["id"]: p for p in json.load(open(SUMBER, encoding="utf-8"))}
    produk = json.load(open(DATA, encoding="utf-8"))
    os.makedirs(DEST, exist_ok=True)

    belum = [p for p in produk if not p.get("gambar")]
    print(f"produk: {len(produk)} | belum ada gambar: {len(belum)}", flush=True)

    ok = gagal = langkau = 0
    for i, p in enumerate(produk, 1):
        if p.get("gambar"):
            langkau += 1
            continue

        src = sumber.get(p["id"], {})
        imgs = src.get("images") or []
        if not imgs or not imgs[0].get("src"):
            gagal += 1
            continue

        keluar = os.path.join(DEST, f"{p['slug']}.webp")
        try:
            req = urllib.request.Request(imgs[0]["src"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
            tmp = "/tmp/_img_dl"
            open(tmp, "wb").write(raw)

            im = Image.open(tmp)
            if im.mode in ("RGBA", "P", "LA"):
                im = im.convert("RGB")
            im.thumbnail((MAKS, MAKS))
            im.save(keluar, "WEBP", quality=KUALITI, method=6)
            p["gambar"] = f"/gambar/{p['slug']}.webp"
            ok += 1
        except Exception as e:
            gagal += 1
            if gagal <= 5:
                print(f"  ! gagal {p['slug'][:40]}: {str(e)[:70]}", flush=True)

        if i % 50 == 0:
            print(f"  {i}/{len(produk)} — ok {ok}, gagal {gagal}", flush=True)
            json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

        time.sleep(JEDA)

    json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ada = sum(1 for p in produk if p.get("gambar"))
    print(f"\nSELESAI — muat turun {ok}, gagal {gagal}, dilangkau {langkau}", flush=True)
    print(f"jumlah produk ada gambar: {ada}/{len(produk)}", flush=True)


if __name__ == "__main__":
    main()
