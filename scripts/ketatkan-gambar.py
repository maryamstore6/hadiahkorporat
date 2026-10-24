#!/usr/bin/env python3
"""
Ketatkan fail gambar sedia ada tanpa muat turun semula.

cover 900  q82 -> q76     (33.3 KB -> ~27 KB)
galeri 700 q78 -> q74     (16.9 KB -> ~14 KB)

Dimensi tidak diubah, jadi tiada perbezaan ketara pada skrin; hanya berat.

Guna:  python3 scripts/ketatkan-gambar.py [--tulis]
"""

import os
import re
import sys

from PIL import Image

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public/gambar")

# Semua slug mengandungi sengkang, jadi padanan mesti tepat pada AKHIRAN nama,
# bukan sekadar ujian "ada sengkang".
GALERI = re.compile(r"-g\d+\.webp$")
THUMB = re.compile(r"-g\d+-t\.webp$")
COVER_VARIAN = re.compile(r"-(300|600)\.webp$")


def kualiti_untuk(nama):
    if THUMB.search(nama):
        return None                       # thumbnail sudah kecil
    if GALERI.search(nama):
        return 74                         # galeri 700px
    if COVER_VARIAN.search(nama):
        return None                       # 300/600 sudah optimum
    if nama.endswith(".webp"):
        return 76                         # cover 900px
    return None


def main():
    tulis = "--tulis" in sys.argv
    fail = [f for f in os.listdir(D) if f.endswith(".webp")]
    jumlah_asal = jumlah_baru = 0
    diproses = 0

    for f in fail:
        q = kualiti_untuk(f)
        if q is None:
            continue
        p = os.path.join(D, f)
        asal = os.path.getsize(p)
        jumlah_asal += asal
        if not tulis:
            diproses += 1
            continue
        try:
            im = Image.open(p)
            im.load()
            im.save(p, "WEBP", quality=q, method=6)
            jumlah_baru += os.path.getsize(p)
            diproses += 1
        except Exception as e:
            jumlah_baru += asal
            print(f"  ! {f}: {str(e)[:50]}")
        if diproses % 500 == 0:
            print(f"  {diproses}…", flush=True)

    if tulis:
        print(f"\n{diproses} fail diproses")
        print(f"  sebelum: {jumlah_asal/1024/1024:.1f} MB")
        print(f"  selepas: {jumlah_baru/1024/1024:.1f} MB")
        print(f"  jimat:   {(jumlah_asal-jumlah_baru)/1024/1024:.1f} MB ({(1-jumlah_baru/max(1,jumlah_asal))*100:.0f}%)")
    else:
        print(f"{diproses} fail akan diproses (dry run — tambah --tulis)")


if __name__ == "__main__":
    main()
