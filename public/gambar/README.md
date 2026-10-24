# Folder gambar produk

Letak gambar produk di sini (jpg/png/webp), kemudian jalankan:

```bash
python3 scripts/pasang-gambar.py <folder-gambar> --tulis
./scripts/deploy.sh "Tambah gambar produk"
```

Nama fail mesti sama dengan **slug** atau **kod produk**, contoh:

- `aluminium-plaque-wp60.jpg` (slug)
- `WP60.jpg` (kod produk)

Skrip akan optimize (maks 900px, WebP) dan menulis medan `gambar` dalam `produk.json`.
