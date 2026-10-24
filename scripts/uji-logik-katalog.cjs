// Uji logik penapis katalog terhadap data SEBENAR dari dist/katalog/index.html
const fs = require('fs');

const html = fs.readFileSync('/home/ubuntu/hadiahkorporat/dist/katalog/index.html', 'utf8');
// muatkan SEMUA produk dari payload
const m = html.match(/<script type="application\/json" id="data-produk">([\s\S]*?)<\/script>/);
if (!m) { console.log('GAGAL cari data-produk'); process.exit(1); }
const SEMUA = JSON.parse(m[1]);
console.log(`produk dimuatkan: ${SEMUA.length}`);
const GANDA = 1.5;
const duit = (n) => 'RM' + Number(n).toLocaleString('ms-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// --- fungsi sama seperti dalam katalog.astro ---
function teks(s) {
  return (s || '').toLowerCase().replace(/[\u2013\u2014]/g, '-').replace(/\s+/g, ' ');
}
function slugKat(s) {
  return (s || '').toLowerCase().replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
}
function tapis(n, qRaw) {
  const q = teks(qRaw.trim());
  return SEMUA.filter((p) => {
    if (n.kat && p.k !== n.kat) return false;
    const lo = p.h, hi = p.hm > p.h ? p.hm : p.h;
    if (n.min !== null && n.min !== undefined && !(hi > 0 && hi >= n.min)) return false;
    if (n.maks !== null && n.maks !== undefined && !(lo > 0 && lo <= n.maks)) return false;
    if (q && !(teks(p.n).includes(q) || teks(p.c).includes(q))) return false;
    return true;
  });
}
const hargaKad = (p) => p.h > 0 ? (p.hm > p.h ? `${duit(p.h)} – ${duit(p.hm)}` : duit(p.h)) : 'Sebut harga';

let lulus = 0, gagal = 0;
function uji(nama, syarat, bukti) {
  if (syarat) { lulus++; console.log(`  LULUS  ${nama}  ${bukti || ''}`); }
  else { gagal++; console.log(`  GAGAL  ${nama}  ${bukti || ''}`); }
}

const berjulat = SEMUA.filter((p) => p.hm > p.h);
console.log(`produk berjulat: ${berjulat.length}\n`);

console.log('=== B1: kad tunjuk julat harga ===');
const c3869 = SEMUA.find((p) => p.c === 'CP3869');
uji('CP3869 papar julat', hargaKad(c3869).includes('–'), hargaKad(c3869));
const satu = SEMUA.find((p) => p.h > 0 && !(p.hm > p.h));
uji('produk satu harga tiada julat', !hargaKad(satu).includes('–'), hargaKad(satu));

console.log('\n=== B2: tapis bajet ambil kira julat ===');
const min100 = tapis({ kat: '', min: 100, maks: null }, '');
const patutAda = berjulat.filter((p) => p.hm >= 100 && p.h < 100);
let semuaAda = patutAda.every((p) => min100.some((x) => x.s === p.s));
uji('min=100 sertakan produk yang ada varian >=100', semuaAda,
  `${patutAda.length} produk, contoh: ${patutAda.slice(0, 3).map((p) => `${p.c}(${p.h}-${p.hm})`).join(', ')}`);

const maks60 = tapis({ kat: '', min: null, maks: 60 }, '');
const patutTiada = berjulat.filter((p) => p.h > 60);
let tiadaSalah = patutTiada.every((p) => !maks60.some((x) => x.s === p.s));
uji('maks=60 TIDAK sertakan produk yang minimum >60', tiadaSalah,
  `${patutTiada.length} produk minimum >60`);

console.log('\n=== B3: ruang berlebihan ===');
const a1 = tapis({}, 'aluminium plaque').length;
const a2 = tapis({}, 'aluminium  plaque').length;
uji('ruang berganda = hasil sama', a1 === a2 && a1 > 0, `1 ruang=${a1}, 2 ruang=${a2}`);

console.log('\n=== B4: en-dash vs hyphen ===');
const d1 = tapis({}, 'straw set – straw1080').length;
const d2 = tapis({}, 'straw set - straw1080').length;
uji('hyphen jumpa en-dash', d1 === d2 && d1 > 0, `en-dash=${d1}, hyphen=${d2}`);

console.log('\n=== B5: ?kategori terima slug ===');
const namaKat = [...new Set(SEMUA.map((p) => p.k))];
const slugUji = 'eco-bag';
const jumpa = namaKat.find((n) => slugKat(n) === slugKat(slugUji));
uji('slug eco-bag dipetakan ke nama sebenar', !!jumpa, `-> "${jumpa}"`);
const kHasil = tapis({ kat: jumpa || '' }, '').length;
uji('tapis ikut slug beri hasil', kHasil > 0, `${kHasil} produk`);

console.log('\n=== B6: ?maks kosong/abc tidak kosongkan grid ===');
const nombor = (v) => {
  if (v === null || v === undefined || String(v).trim() === '') return null;
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? n : null;
};
uji('maks tiada (null) -> null, BUKAN 0', nombor(null) === null, `nombor(null)=${nombor(null)}`);
uji('maks="" -> null', nombor('') === null, `nombor('')=${nombor('')}`);
uji('maks=abc -> null', nombor('abc') === null, `nombor('abc')=${nombor('abc')}`);
uji('maks=60 -> 60', nombor('60') === 60, `nombor('60')=${nombor('60')}`);
// regresi: URL tanpa parameter TIDAK boleh menapis semua produk keluar
const asas = tapis({ kat: '', min: nombor(null), maks: nombor(null) }, '');
uji('tanpa tapisan: semua 1,296 produk kekal', asas.length === SEMUA.length, `${asas.length} produk`);

console.log(`\n${lulus} lulus, ${gagal} gagal`);
process.exit(gagal ? 1 : 0);