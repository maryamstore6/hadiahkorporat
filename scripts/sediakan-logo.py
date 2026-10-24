#!/usr/bin/env python3
"""
Sediakan logo jenama untuk web.

Sumber: JPEG 383x382, latar putih tulen, dakwat hijau (~#4BA271).

Menghasilkan (dalam public/):
  logo.png           512px, latar TELUS (untuk kepala laman)
  logo.webp          versi WebP logo.png
  logo-putih.png     512px, dakwat limau (untuk kaki/kepala gelap)
  favicon-32.png
  favicon-64.png
  apple-touch-icon.png  180px, latar putih (iOS tidak sokong telus)
  favicon.ico        16+32+48

Latar putih dibuang dengan "unmultiply": piksel putih menjadi alpha 0 tanpa
menjadikan garis hijau pucat, dan warna dakwat asal dikekalkan.
"""

import os
from PIL import Image

SUMBER = ("/home/ubuntu/.hermes/profiles/utama/cache/documents/native-inputs/"
          "3fefc7432538c3261738f37a319f57ef742de414b342db75e4c951ea60cd5467/img_d656902a9a5a.jpg")
KELUAR = "/home/ubuntu/hadiahkorporat/public"
DAKWAT_LIMAU = (211, 250, 153)   # --lime
DAKWAT_HUTAN = (28, 58, 19)      # --forest (#1c3a13) — sepadan dengan warna teks laman
PADDING = 0.02                    # 2% ruang bernafas di sekeliling


def potong(im):
    """Buang margin putih berlebihan."""
    g = im.convert("L")
    kotak = g.point(lambda v: 255 if v < 200 else 0).getbbox()
    l, t, r, b = kotak
    sisi = max(r - l, b - t)
    cx, cy = (l + r) // 2, (t + b) // 2
    separuh = sisi // 2
    tambah = int(sisi * PADDING)
    kiri = max(0, cx - separuh - tambah)
    atas = max(0, cy - separuh - tambah)
    kanan = min(im.width, cx + separuh + tambah)
    bawah = min(im.height, cy + separuh + tambah)
    return im.crop((kiri, atas, kanan, bawah))


def warna_dakwat(im):
    """Warna dakwat = median piksel paling gelap (bahagian garis yang pejal)."""
    rgb = im.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    calon = []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if (r * 299 + g * 587 + b * 114) // 1000 < 120:
                calon.append((r, g, b))
    calon.sort(key=lambda c: sum(c))
    n = len(calon)
    if not n:
        return (75, 162, 113)
    return calon[n // 2]


def telus(im, dakwat=None):
    """Putih -> alpha 0. Garis jadi SATU warna rata (logo garis monokrom).

    Membiarkan hingar warna JPEG pada setiap piksel anti-alias menjadikan PNG
    membengkak (~240 KB); meratakan warna mengecilkannya ke beberapa KB tanpa
    perbezaan yang kelihatan.
    """
    if dakwat is None:
        dakwat = warna_dakwat(im)
    rgb = im.convert("RGB")
    hasil = Image.new("RGBA", rgb.size, dakwat + (0,))
    src, dst = rgb.load(), hasil.load()
    w, h = rgb.size
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            lum = (r * 299 + g * 587 + b * 114) // 1000
            # 150 (bukan 190): garis nipis kekal lebih pejal pada saiz paparan kecil
            a = int(max(0, min(255, round((255 - lum) * 255 / 150))))
            if a:
                dst[x, y] = dakwat + (a,)
    return hasil


def warnakan(im_telus, warna):
    """Ganti semua dakwat dengan satu warna, kekalkan alpha."""
    hasil = Image.new("RGBA", im_telus.size, warna + (0,))
    hasil.putalpha(im_telus.split()[3])
    return hasil


def main():
    im = Image.open(SUMBER)
    print("sumber:", im.size)
    im = potong(im)
    print("selepas potong:", im.size)

    dakwat = warna_dakwat(im)
    print("warna dakwat dikesan:", dakwat)
    t = telus(im, dakwat)
    t256 = t.resize((256, 256), Image.LANCZOS)
    t256.save(os.path.join(KELUAR, "logo.png"), optimize=True)
    t256.save(os.path.join(KELUAR, "logo.webp"), "WEBP", quality=92, method=6)
    print("logo.png / logo.webp:", os.path.getsize(os.path.join(KELUAR, "logo.png")) // 1024, "KB")

    # Varian kecil untuk kepala laman (dipapar ~36px; 128px cukup untuk retina 3x)
    t128 = t.resize((128, 128), Image.LANCZOS)
    hutan = warnakan(t128, DAKWAT_HUTAN)
    hutan.save(os.path.join(KELUAR, "logo-128.png"), optimize=True)
    hutan.save(os.path.join(KELUAR, "logo-128.webp"), "WEBP", quality=92, method=6)
    # Simpan juga versi hijau asal, untuk tukar jika mahu
    t128.save(os.path.join(KELUAR, "logo-128-asal.png"), optimize=True)

    limau = warnakan(t256, DAKWAT_LIMAU)
    limau.save(os.path.join(KELUAR, "logo-putih.png"), optimize=True)
    print("logo-putih.png dicipta")

    # Ikon: perlu latar (iOS/Android tidak tunjuk alpha dengan baik pada semua tempat)
    for saiz in (64, 32):
        ikon = Image.new("RGB", (saiz, saiz), (247, 246, 241))
        lapis = t.resize((int(saiz * 0.86), int(saiz * 0.86)), Image.LANCZOS)
        ofs = (saiz - lapis.width) // 2
        ikon.paste(lapis, (ofs, ofs), lapis)
        ikon.save(os.path.join(KELUAR, f"favicon-{saiz}.png"), optimize=True)

    apple = Image.new("RGB", (180, 180), (247, 246, 241))
    lapis = t.resize((150, 150), Image.LANCZOS)
    apple.paste(lapis, (15, 15), lapis)
    apple.save(os.path.join(KELUAR, "apple-touch-icon.png"), optimize=True)

    # favicon.ico berbilang saiz
    ikon_ico = Image.new("RGB", (64, 64), (247, 246, 241))
    lapis = t.resize((54, 54), Image.LANCZOS)
    ikon_ico.paste(lapis, (5, 5), lapis)
    ikon_ico.save(os.path.join(KELUAR, "favicon.ico"),
                  sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

    print("\n--- semua aset ---")
    for f in ("logo.png", "logo.webp", "logo-128.png", "logo-128.webp", "logo-putih.png", "favicon-32.png",
              "favicon-64.png", "apple-touch-icon.png", "favicon.ico"):
        p = os.path.join(KELUAR, f)
        if os.path.exists(p):
            print(f"  {f:<24} {os.path.getsize(p)/1024:>7.1f} KB")


if __name__ == "__main__":
    main()
