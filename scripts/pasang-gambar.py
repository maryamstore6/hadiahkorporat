#!/usr/bin/env python3
"""
Pasang gambar produk ke dalam katalog.

Cara guna:
    python3 scripts/pasang-gambar.py <folder-gambar> [--tulis]

Fail gambar dinamakan mengikut SALAH SATU:
    <slug-produk>.jpg      cth.  aluminium-plaque-wp60.jpg
    <kod-produk>.jpg       cth.  WP60.jpg

Ia akan:
  1. Optimize setiap gambar (maks 900px, WebP kualiti 82)
  2. Simpan ke public/gambar/<slug>.webp
  3. Tulis medan "gambar" dalam src/data/produk.json

Tanpa --tulis, ia hanya LAPOR apa yang akan berlaku (dry run).
"""

import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("PIL tiada. Jalankan: pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "src/data/produk.json")
DEST = os.path.join(ROOT, "public/gambar")
MAKS = 900
KUALITI = 82

SAIZ_SAH = (".jpg", ".jpeg", ".png", ".webp", ".avif")


def kunci(s):
    """Normalkan nama untuk padanan: huruf kecil, buang bukan-alfanumerik."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    tulis = "--tulis" in sys.argv
    if not os.path.isdir(src):
        sys.exit(f"Folder tidak dijumpai: {src}")

    produk = json.load(open(DATA, encoding="utf-8"))

    # Indeks padanan: slug penuh + kod produk
    ikut_slug = {kunci(p["slug"]): p for p in produk}
    ikut_sku = {kunci(p["sku"]): p for p in produk if p.get("sku")}

    fail = sorted(f for f in os.listdir(src) if f.lower().endswith(SAIZ_SAH))
    if not fail:
        sys.exit(f"Tiada fail gambar dalam {src}")

    os.makedirs(DEST, exist_ok=True)
    padan, tak_padan = 0, []

    for nama in fail:
        k = kunci(os.path.splitext(nama)[0])
        p = ikut_slug.get(k) or ikut_sku.get(k)
        if not p:
            tak_padan.append(nama)
            continue

        nama_out = f"{p['slug']}.webp"
        laluan_out = os.path.join(DEST, nama_out)
        if tulis:
            im = Image.open(os.path.join(src, nama))
            if im.mode in ("RGBA", "P", "LA"):
                latar = Image.new("RGB", im.size, (255, 255, 255))
                latar.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
                im = latar
            else:
                im = im.convert("RGB")
            im.thumbnail((MAKS, MAKS))
            im.save(laluan_out, "WEBP", quality=KUALITI, method=6)
            p["gambar"] = f"/gambar/{nama_out}"

        padan += 1
        print(f"  ✓ {nama:<44} → {p['nama'][:42]}")

    print(f"\nDipadankan: {padan}/{len(fail)}")
    if tak_padan:
        print(f"Tidak dipadankan ({len(tak_padan)}) — nama fail mesti sama dengan slug atau kod produk:")
        for n in tak_padan[:15]:
            print(f"  · {n}")

    if tulis:
        json.dump(produk, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"\nproduk.json dikemas kini ({sum(1 for p in produk if p.get('gambar'))} produk ada gambar)")
        print("Seterusnya: ./scripts/deploy.sh \"Tambah gambar produk\"")
    else:
        print("\n(Ini dry run — tambah --tulis untuk benar-benar menulis)")


if __name__ == "__main__":
    main()
