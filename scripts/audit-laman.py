#!/usr/bin/env python3
"""
Audit menyeluruh laman bina: pautan, gambar, aset, dan struktur.

Merayau SEMUA fail HTML dalam dist/ dan menyemak setiap pautan dalaman,
setiap gambar (termasuk srcset), dan setiap aset <link>/<script> —
memastikan sasarannya benar-benar wujud dalam dist/.

Keluaran: /tmp/audit-laman.json + ringkasan di stdout.

Ini kerja mekanikal: setiap rujukan diperiksa terhadap fail sebenar,
bukan diandaikan.
"""

import json
import os
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
BASE = "/hadiahkorporat"


class Kumpul(HTMLParser):
    """Kumpul pautan, gambar dan aset dari satu fail HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pautan = []      # (href, teks_anchor)
        self.gambar = []      # src
        self.srcset = []      # senarai url
        self.aset = []        # css/js
        self.ids = set()
        self.section = []
        self._dalam_a = False
        self._teks_a = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            self._dalam_a = True
            self._teks_a = []
            if a.get("href"):
                self.pautan.append(a["href"])
        elif tag == "img":
            if a.get("src"):
                self.gambar.append(a["src"])
            if a.get("srcset"):
                for bahagian in a["srcset"].split(","):
                    u = bahagian.strip().split(" ")[0]
                    if u:
                        self.srcset.append(u)
        elif tag == "source":
            if a.get("srcset"):
                for bahagian in a["srcset"].split(","):
                    u = bahagian.strip().split(" ")[0]
                    if u:
                        self.srcset.append(u)
        elif tag == "link":
            if a.get("href") and (a.get("rel") or "") in ("stylesheet", "preload", "icon"):
                self.aset.append(a["href"])
        elif tag == "script":
            if a.get("src"):
                self.aset.append(a["src"])
        elif tag == "section":
            self.section.append(a.get("class") or a.get("id") or "?")

    def handle_endtag(self, tag):
        if tag == "a":
            self._dalam_a = False

    def handle_data(self, data):
        if self._dalam_a:
            self._teks_a.append(data)


def wujud(url):
    """Adakah URL dalaman ini wujud sebagai fail dalam dist/?"""
    laluan = unquote(urlparse(url).path)
    if not laluan.startswith(BASE):
        return True                      # luaran — tidak diperiksa di sini
    relatif = laluan[len(BASE):].lstrip("/")
    if relatif == "" or relatif.endswith("/"):
        relatif += "index.html"
    calon = os.path.join(DIST, relatif)
    if os.path.isfile(calon):
        return True
    if os.path.isfile(os.path.join(DIST, relatif, "index.html")):
        return True
    return False


def main():
    halaman = []
    for akar, _, fail in os.walk(DIST):
        for f in fail:
            if f.endswith(".html"):
                halaman.append(os.path.join(akar, f))
    halaman.sort()
    print(f"{len(halaman)} fail HTML dalam dist/\n", flush=True)

    rosak_pautan = []
    rosak_gambar = []
    rosak_aset = []
    anchor_rosak = []
    tanpa_alt = 0
    jumlah_gambar = 0

    for i, h in enumerate(halaman, 1):
        url_halaman = "/" + os.path.relpath(h, DIST).replace("index.html", "")
        try:
            html = open(h, encoding="utf-8").read()
        except Exception as e:
            rosak_pautan.append((url_halaman, f"gagal baca: {e}"))
            continue

        p = Kumpul()
        p.feed(html)

        # pautan
        for href in p.pautan:
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:")):
                if href.startswith("#") and len(href) > 1:
                    if href[1:] not in p.ids:
                        anchor_rosak.append((url_halaman, href))
                continue
            if not wujud(href):
                rosak_pautan.append((url_halaman, href))

        # gambar + srcset
        semua_gambar = p.gambar + p.srcset
        for src in semua_gambar:
            jumlah_gambar += 1
            if src.startswith("http") or src.startswith("data:"):
                continue
            if not wujud(src):
                rosak_gambar.append((url_halaman, src))

        # aset
        for a in p.aset:
            if a.startswith("http") or a.startswith("data:"):
                continue
            if not wujud(a):
                rosak_aset.append((url_halaman, a))

        # alt
        for m in re.finditer(r"<img\b[^>]*>", html):
            if "alt=" not in m.group(0):
                tanpa_alt += 1

        if i % 300 == 0:
            print(f"  {i}/{len(halaman)} …", flush=True)

    # --- ringkasan ---
    hasil = {
        "halaman": len(halaman),
        "gambar_diperiksa": jumlah_gambar,
        "pautan_rosak": rosak_pautan,
        "gambar_rosak": rosak_gambar,
        "aset_rosak": rosak_aset,
        "anchor_rosak": anchor_rosak,
        "img_tanpa_alt": tanpa_alt,
    }
    json.dump(hasil, open("/tmp/audit-laman.json", "w"), ensure_ascii=False, indent=1)

    def keluar(nama, senarai):
        unik = sorted(set(senarai))
        print(f"\n{nama}: {len(unik)} unik")
        for u, t in unik[:15]:
            print(f"   {u[:60]:62s} -> {t[:70]}")

    print("\n" + "=" * 70)
    print(f"halaman diperiksa : {len(halaman)}")
    print(f"gambar diperiksa  : {jumlah_gambar}")
    keluar("PAUTAN ROSAK", rosak_pautan)
    keluar("GAMBAR HILANG", rosak_gambar)
    keluar("ASET HILANG", rosak_aset)
    keluar("ANCHOR ROSAK", anchor_rosak)
    print(f"\n<img> tanpa alt   : {tanpa_alt}")


if __name__ == "__main__":
    main()
