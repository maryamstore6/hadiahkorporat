#!/usr/bin/env python3
"""
Cari gambar cover produk yang 'pecah' — hampir seluruhnya putih,
terlalu kecil, atau hampir kosong.

Gambar produk pembekal selalunya ada latar putih, jadi 'putih' bukan
kesalahan dengan sendirinya. Yang menjadi masalah ialah apabila produk
itu sendiri terlalu kecil dalam bingkai (jubin nampak kosong).

Ukuran:
  putih%      - peratus piksel hampir putih dalam imej
  kandungan%  - luas kotak sempadan produk berbanding seluruh imej
"""

import json
import os
import sys

from PIL import Image, ImageChops

ROOT = "/home/ubuntu/hadiahkorporat"
produk = json.load(open(f"{ROOT}/src/data/produk.json", encoding="utf-8"))

baris = []
tiada = []
for p in produk:
    g = p.get("gambar")
    if not g:
        tiada.append(p)
        continue
    f = f"{ROOT}/public{g}"
    if not os.path.exists(f):
        tiada.append(p)
        continue
    try:
        im = Image.open(f).convert("RGB")
    except Exception:
        tiada.append(p)
        continue

    kecil = im.copy()
    kecil.thumbnail((160, 160), Image.LANCZOS)
    px = list(kecil.getdata())
    n = len(px)
    putih = sum(1 for r, gg, b in px if r > 245 and gg > 245 and b > 245) / n * 100

    beza = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).convert("L")
    bb = beza.point(lambda v: 255 if v > 10 else 0).getbbox()
    if bb:
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        isi = (w * h) / (im.width * im.height) * 100
        # nisbah kepenuhan selepas muat ke bingkai segi empat
        s = min(1.0 / w, 1.0 / h) if w and h else 0
        penuh = (w * s) * (h * s) * 100
    else:
        isi = penuh = 0

    baris.append((putih, isi, penuh, im.size, p["slug"], p["nama"], p["kategori"], os.path.getsize(f) / 1024))

print(f"produk: {len(produk)} | ada gambar: {len(baris)} | tiada gambar: {len(tiada)}")
print(f"saiz imej: min={min(b[3][0] for b in baris)}x{min(b[3][1] for b in baris)} "
      f"maks={max(b[3][0] for b in baris)}x{max(b[3][1] for b in baris)}\n")

# Taburan
for ambang in (95, 90, 85, 80, 70):
    bil = sum(1 for b in baris if b[0] > ambang)
    print(f"  putih > {ambang}% : {bil} produk")
print()
for ambang in (10, 20, 30, 40):
    bil = sum(1 for b in baris if b[2] < ambang)
    print(f"  kepenuhan < {ambang}% : {bil} produk")

print("\n=== 25 PALING PUTIH ===")
print(f"{'putih%':>7s} {'kand%':>6s} {'penuh%':>7s} {'saiz':>11s} {'KB':>6s}  produk")
for putih, isi, penuh, saiz, slug, nama, kat, kb in sorted(baris, reverse=True)[:25]:
    print(f"{putih:6.1f}% {isi:5.1f}% {penuh:6.1f}% {saiz[0]:>5}x{saiz[1]:<5} {kb:6.1f}  {nama[:42]}")

print("\n=== 15 IMEJ TERLALU KECIL (< 250px) ===")
for putih, isi, penuh, saiz, slug, nama, kat, kb in sorted(baris, key=lambda x: min(x[3]))[:15]:
    print(f"{putih:6.1f}% {isi:5.1f}% {penuh:6.1f}% {saiz[0]:>5}x{saiz[1]:<5} {kb:6.1f}  {nama[:42]}")

if tiada:
    print(f"\n=== {len(tiada)} PRODUK TIADA GAMBAR ===")
    for p in tiada[:10]:
        print(f"   {p['nama'][:56]}")
