#!/usr/bin/env python3
"""
Jana varian saiz gambar untuk paparan responsif.

Untuk setiap public/gambar/<slug>.webp (900px), jana:
    <slug>-600.webp   600px  (tablet)
    <slug>-300.webp   300px  (telefon — 2 lajur)

Kad telefon selebar ~180px; menghantar gambar 900px ke telefon membazir ~4x
data. Varian 300px memotong muat turun katalog telefon dari ~1.2 MB ke ~0.3 MB.

Skrip ini BOLEH dijalankan semula: varian yang sudah ada dilangkau.
"""

import os
import sys
import time

try:
    from PIL import Image
except ImportError:
    sys.exit("PIL tiada. Jalankan: pip install Pillow")

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public/gambar")
VARIAN = [(600, 80), (300, 78)]


def main():
    asas = sorted(
        f for f in os.listdir(D)
        if f.endswith(".webp") and not any(f.endswith(f"-{w}.webp") for w, _ in VARIAN)
    )
    print(f"gambar asas: {len(asas)}", flush=True)

    mula = time.time()
    dibuat = dilangkau = 0
    for i, f in enumerate(asas, 1):
        src = os.path.join(D, f)
        batang = f[:-5]
        for lebar, kualiti in VARIAN:
            keluar = os.path.join(D, f"{batang}-{lebar}.webp")
            if os.path.exists(keluar):
                dilangkau += 1
                continue
            im = Image.open(src)
            if im.width <= lebar:
                im.save(keluar, "WEBP", quality=kualiti, method=6)
            else:
                salinan = im.copy()
                salinan.thumbnail((lebar, lebar), Image.LANCZOS)
                salinan.save(keluar, "WEBP", quality=kualiti, method=6)
            dibuat += 1
        if i % 150 == 0:
            print(f"  {i}/{len(asas)} — dibuat {dibuat}", flush=True)

    jumlah = sum(os.path.getsize(os.path.join(D, x)) for x in os.listdir(D) if x.endswith(".webp"))
    print(f"\nSELESAI dalam {time.time()-mula:.0f}s — dibuat {dibuat}, dilangkau {dilangkau}", flush=True)
    print(f"jumlah fail: {len([x for x in os.listdir(D) if x.endswith('.webp')])} | saiz folder: {jumlah/1024/1024:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
