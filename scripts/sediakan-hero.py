#!/usr/bin/env python3
"""
Sediakan gambar hero untuk web — AVIF (utama) + WebP (sandaran).

Sumber: JPEG 1254x1254.
Keluaran (public/hero/):
    hero-480.avif / .webp    telefon (DPR 1-2)
    hero-720.avif / .webp    telefon retina / tablet
    hero-960.avif / .webp    desktop retina

Kenapa dua format: AVIF 30-40% lebih kecil daripada WebP pada kualiti yang
sama, tetapi WebP masih perlu sebagai sandaran untuk pelayar lama. `<picture>`
membolehkan pelayar pilih sendiri — ia muat turun SATU fail sahaja.

Guna: python3 scripts/sediakan-hero.py <laluan-gambar>
"""

import os
import sys

from PIL import Image

KELUAR = "/home/ubuntu/hadiahkorporat/public/hero"
SAIZ = [(960, 50, 76), (720, 50, 76), (480, 50, 76)]   # (lebar, kualiti AVIF, kualiti WebP)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    if not os.path.exists(src):
        sys.exit(f"Tiada: {src}")

    im = Image.open(src)
    print(f"sumber: {im.size} {im.mode} {im.format} ({os.path.getsize(src)/1024:.0f} KB)")
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGB")

    os.makedirs(KELUAR, exist_ok=True)
    jum_avif = jum_webp = 0

    for lebar, q_avif, q_webp in SAIZ:
        s = im.copy()
        s.thumbnail((lebar, lebar), Image.LANCZOS)

        f_avif = os.path.join(KELUAR, f"hero-{lebar}.avif")
        s.save(f_avif, "AVIF", quality=q_avif)
        a = os.path.getsize(f_avif)
        jum_avif += a

        f_webp = os.path.join(KELUAR, f"hero-{lebar}.webp")
        s.save(f_webp, "WEBP", quality=q_webp, method=6)
        w = os.path.getsize(f_webp)
        jum_webp += w

        print(f"  {lebar}px  {s.size[0]}x{s.size[1]}  AVIF {a/1024:>5.1f} KB  |  WebP {w/1024:>5.1f} KB")

    print(f"\nAVIF kesemuanya: {jum_avif/1024:.1f} KB | WebP kesemuanya: {jum_webp/1024:.1f} KB")
    print("Pelayar muat turun SATU fail sahaja (biasanya AVIF 480-960px = 12-35 KB)")


if __name__ == "__main__":
    main()
