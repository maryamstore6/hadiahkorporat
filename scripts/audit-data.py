#!/usr/bin/env python3
"""Audit data produk + halaman kategori. Semua keputusan dari fail sebenar."""

import collections
import glob
import json
import os
import re

from PIL import Image

ROOT = "/home/ubuntu/hadiahkorporat"
produk = json.load(open(f"{ROOT}/src/data/produk.json", encoding="utf-8"))
DIST = f"{ROOT}/dist"

print("=" * 72)
print(f"AUDIT DATA PRODUK — {len(produk)} rekod")
print("=" * 72)

# 1 & 2: slug / id duplikat
slug = collections.Counter(p["slug"] for p in produk)
idp = collections.Counter(p["id"] for p in produk)
dup_slug = [s for s, n in slug.items() if n > 1]
dup_id = [i for i, n in idp.items() if n > 1]
print(f"\n1. slug duplikat : {len(dup_slug)} {dup_slug[:5]}")
print(f"2. id duplikat   : {len(dup_id)} {dup_id[:5]}")

# 3: harga 0 / tiada
tanpa_harga = [p for p in produk if not p.get("harga")]
print(f"\n3. harga 0/tiada : {len(tanpa_harga)}")
contoh = tanpa_harga[:5]
for p in contoh:
    print(f"     {p['slug'][:50]:52s} harga={p.get('harga')}")

# 4: harga_max mesti > harga
julat = [p for p in produk if p.get("harga_max")]
salah = [p for p in julat if p["harga_max"] <= p["harga"]]
print(f"\n4. produk berjulat: {len(julat)} | harga_max salah: {len(salah)}")
for p in salah[:5]:
    print(f"     {p['slug'][:44]:46s} {p['harga']} -> {p['harga_max']}")

# 5 & 6: gambar / galeri hilang
g_hilang = [p for p in produk if p.get("gambar")
            and not os.path.exists(f"{ROOT}/public{p['gambar']}")]
tanpa_gambar = [p for p in produk if not p.get("gambar")]
gal_hilang = []
for p in produk:
    for g in (p.get("galeri") or []):
        if not os.path.exists(f"{ROOT}/public{g}"):
            gal_hilang.append((p["slug"], g))
            break
print(f"\n5. gambar medan ada tetapi fail TIADA : {len(g_hilang)} {[p['slug'][:34] for p in g_hilang[:5]]}")
print(f"   produk tanpa medan gambar          : {len(tanpa_gambar)}")
print(f"6. galeri medan ada tetapi fail TIADA : {len(gal_hilang)} {[x[0][:30] for x in gal_hilang[:5]]}")

# 7: nama kosong / terlalu panjang
nama_kosong = [p for p in produk if not (p.get("nama") or "").strip()]
nama_panjang = [p for p in produk if len(p.get("nama") or "") > 120]
print(f"\n7. nama kosong   : {len(nama_kosong)} | nama >120 aksara: {len(nama_panjang)}")
for p in nama_panjang[:3]:
    print(f"     {len(p['nama'])} aksara: {p['nama'][:90]}")

# 8: kategori kosong / ejaan tak konsisten
kats = collections.Counter(p["kategori"] for p in produk)
kosong = [k for k in kats if not k.strip()]
print(f"\n8. kategori: {len(kats)} | kosong: {len(kosong)}")
# kesan pasangan yang mungkin sama (beza huruf besar/kecil atau tanda)
norm = collections.defaultdict(list)
for k in kats:
    norm[re.sub(r"[^a-z0-9]", "", k.lower())].append(k)
hampir = {a: v for a, v in norm.items() if len(v) > 1}
print(f"   pasangan hampir sama: {len(hampir)}")
for a, v in list(hampir.items())[:6]:
    print(f"     {v}  -> {[kats[x] for x in v]} produk")

# 9: halaman produk berjulat memaparkan julat
print("\n9. Semakan halaman HTML produk berjulat:")
for p in julat[:5]:
    f = f"{DIST}/produk/{p['slug']}/index.html"
    if not os.path.exists(f):
        print(f"     TIADA FAIL: {p['slug']}")
        continue
    h = open(f, encoding="utf-8").read()
    ada_julat = ("–" in h and f"RM{p['harga']:.2f}" in h and f"RM{p['harga_max']:.2f}" in h)
    ada_nota = "Harga bergantung pada pilihan" in h
    print(f"     {'OK ' if ada_julat else 'GAGAL'} julat={ada_julat} nota={ada_nota}  {p['slug'][:40]}")

# --- HALAMAN KATEGORI ---
print("\n" + "=" * 72)
print("AUDIT HALAMAN KATEGORI")
print("=" * 72)

slug_kat = {k: (json.load(open(f"{ROOT}/public/kategori/_indeks.json", encoding="utf-8"))
                .get(k) or {}).get("slug") for k in kats}
indeks = json.load(open(f"{ROOT}/public/kategori/_indeks.json", encoding="utf-8"))

tiada_halaman, tiada_gambar, putih_tinggi, agak_putih = [], [], [], []
for k in sorted(kats):
    slug_k = indeks.get(k, {}).get("slug")
    if not slug_k:
        tiada_halaman.append(k)
        continue
    if not os.path.exists(f"{DIST}/kategori/{slug_k}/index.html"):
        tiada_halaman.append(k)
    for saiz in (400, 800):
        f = f"{ROOT}/public/kategori/{slug_k}-{saiz}.webp"
        if not os.path.exists(f):
            tiada_gambar.append((k, saiz))
    f400 = f"{ROOT}/public/kategori/{slug_k}-400.webp"
    if os.path.exists(f400):
        im = Image.open(f400).convert("RGB")
        kecil = im.copy()
        kecil.thumbnail((160, 160), Image.LANCZOS)
        px = list(kecil.getdata())
        pp = sum(1 for r, g, b in px if r > 245 and g > 245 and b > 245) / len(px) * 100
        if pp > 85:
            putih_tinggi.append((k, pp))
        elif pp > 75:
            agak_putih.append((k, pp))

print(f"\n1. kategori sepatutnya: {len(kats)} | tiada halaman: {len(tiada_halaman)} {tiada_halaman}")
print(f"2. gambar hilang: {len(tiada_gambar)} {tiada_gambar[:5]}")
print(f"3. >85% putih: {len(putih_tinggi)} | 75-85%: {len(agak_putih)}")
for k, pp in putih_tinggi:
    print(f"     KOSONG  {k[:34]:36s} {pp:.1f}%")
for k, pp in agak_putih:
    print(f"     waspada {k[:34]:36s} {pp:.1f}%")

# 4: bilangan kad produk pada halaman kategori vs sebenar
print("\n4. Bilangan produk dipapar vs sebenar (8 kategori):")
uji = sorted(kats, key=lambda x: -kats[x])[:8]
for k in uji:
    slug_k = indeks.get(k, {}).get("slug")
    f = f"{DIST}/kategori/{slug_k}/index.html"
    if not os.path.exists(f):
        print(f"     TIADA HALAMAN {k}")
        continue
    h = open(f, encoding="utf-8").read()
    bil = h.count('class="card"')
    sebenar = kats[k]
    tanda = "OK " if bil >= min(sebenar, 24) else "?"
    print(f"     {tanda} {k[:30]:32s} kad={bil:4d} sebenar={sebenar:4d}")

# 5: halaman kategori kosong
kosong_h = []
for k in kats:
    slug_k = indeks.get(k, {}).get("slug")
    f = f"{DIST}/kategori/{slug_k}/index.html"
    if os.path.exists(f) and open(f, encoding="utf-8").read().count('class="card"') == 0:
        kosong_h.append(k)
print(f"\n5. halaman kategori kosong: {len(kosong_h)} {kosong_h[:5]}")

print("\nSELESAI.")
