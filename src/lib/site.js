import produk from '../data/produk.json';

/* ============================================================
   Tetapan laman — ubah di sini sahaja
   ============================================================ */
export const SITE = {
  // ⚠️ Tukar kepada nama jenama sebenar anda
  nama: 'HadiahKorporat',
  namaPendek: 'HK',
  tagline: 'Hadiah korporat bercetak logo, dihantar terus dari kilang.',
  // ⚠️ Tukar kepada nombor WhatsApp bisnes anda (format antarabangsa, tiada +)
  whatsapp: '60176055349',
  emel: 'hello@hadiahkorporat.my',
  negeri: 'Melaka, Malaysia',
  moq: 10,
};

export const produkSemua = produk;

/* ---------- Kategori ---------- */
export function kategoriSemua() {
  const map = new Map();
  for (const p of produk) {
    if (!map.has(p.kategori)) map.set(p.kategori, 0);
    map.set(p.kategori, map.get(p.kategori) + 1);
  }
  return [...map.entries()]
    .map(([nama, bilangan]) => ({ nama, bilangan, slug: slugify(nama) }))
    .sort((a, b) => b.bilangan - a.bilangan);
}

export function produkKategori(slug) {
  return produk.filter((p) => slugify(p.kategori) === slug);
}

/* ---------- Warna kategori (untuk jubin pengganti gambar) ---------- */
const PALET = [
  ['#0B5D4F', '#0E7A66'], ['#1F3A5F', '#2C5282'], ['#6B3F2A', '#8A5638'],
  ['#3D2B56', '#54397A'], ['#7A2E3B', '#9C3C4C'], ['#1E4D4A', '#2A6B66'],
  ['#4A4A22', '#6B6B31'], ['#2E3A2E', '#455445'], ['#553322', '#6E442D'],
  ['#243B4A', '#315160'], ['#5A2D5A', '#773C77'], ['#3A3A3A', '#525252'],
];

export function warnaKategori(nama) {
  let h = 0;
  for (let i = 0; i < nama.length; i++) h = (h * 31 + nama.charCodeAt(i)) >>> 0;
  return PALET[h % PALET.length];
}

/* Variasi jubin setiap produk: warna asas ikut kategori, tetapi
   sudut dan ton berbeza supaya kad bersebelahan tidak kelihatan serupa. */
export function warnaProduk(nama, kategori) {
  const [c1, c2] = warnaKategori(kategori);
  let h = 0;
  for (let i = 0; i < nama.length; i++) h = (h * 37 + nama.charCodeAt(i)) >>> 0;
  const sudut = 120 + (h % 5) * 30;          // 120–240 darjah
  const gelap = ['#00000022', '#ffffff18', '#00000010', '#ffffff22'][h % 4];
  return { c1, c2, sudut, lapis: gelap };
}

export function inisial(nama) {
  const buang = /^(the|dan|and|with|for|fully|in|1|2|3)\s+/i;
  const bersih = nama.replace(/\(.*?\)/g, ' ').replace(buang, '').trim();
  const perkataan = bersih.split(/[\s\-–—/]+/).filter((w) => /[a-zA-Z]/.test(w));
  return perkataan.slice(0, 2).map((w) => w[0].toUpperCase()).join('') || 'HK';
}

/* ---------- Utiliti ---------- */
export function slugify(s) {
  return String(s)
    .toLowerCase()
    .replace(/&amp;/g, 'and')
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 70);
}

/* Gambar wakil kategori: /kategori/<slug>-400.webp dan -800.webp */
export function gambarKategori(nama, saiz = 400) {
  return `/kategori/${slugify(nama)}-${saiz}.webp`;
}

/* Harga coret (harga "dulu") = harga semasa x ganda ini.
   Ubah di sini sahaja kalau mahu nisbah lain. */
export const GANDA_CORET = 1.5;

export function hargaCoret(n) {
  return Math.round(n * GANDA_CORET * 100) / 100;
}

/* Teks harga: julat kalau pembekal ada beberapa pilihan harga, jika tidak satu harga. */
export function teksHarga(p) {
  if (!p || !(p.harga > 0)) return '';
  if (p.harga_max && p.harga_max > p.harga) {
    return `${duit(p.harga)} – ${duit(p.harga_max)}`;
  }
  return duit(p.harga);
}

export function duit(n) {
  return 'RM' + Number(n).toLocaleString('ms-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/* Varian saiz gambar: <slug>-300.webp / <slug>-600.webp / <slug>.webp */
export function srcset(gambar) {
  const b = gambar.replace(/\.webp$/, '');
  return [
    `${pautan(b + '-300.webp')} 300w`,
    `${pautan(b + '-600.webp')} 600w`,
    `${pautan(gambar)} 900w`,
  ].join(', ');
}

/* Saiz paparan kad produk — telefon 2 lajur, desktop ~240px */
export const SAIZ_KAD = '(max-width: 640px) 45vw, (max-width: 1100px) 30vw, 240px';
export const SAIZ_HERO = '(max-width: 900px) 92vw, 45vw';

export function pautan(p) {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}${p}`;
}
