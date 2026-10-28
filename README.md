# FinancePress — AllAboutMoney.id

Bot artikel finansial: cari topik baru, baca sumber publik, tulis pembahasan panjang,
siapkan kategori/tag/excerpt/gambar AI, lalu preview dan Publish ke WordPress.

**Mulai dari [REVISI-KONTEN.md](REVISI-KONTEN.md)** untuk pembaruan terbaru, perbaikan
artikel yang terbit, slug judul dan pencegahan duplikasi.

## Pasang atau update

Pengguna lama: cadangkan lalu ganti bot.py dan config.json. Pertahankan .env,
.venv dan seluruh folder data. Tidak ada dependensi baru. config.json berisi sumber
lebih luas serta enam kategori situs. Perbaikan login dan gambar sudah termasuk.

Pemasangan baru pada Linux/macOS, Python 3.10+ (Windows: WSL):

```bash
cd financepress
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
```

Isi OPENAI_API_KEY, OPENAI_MODEL, WP_USERNAME dan WP_APP_PASSWORD. WordPress memakai
Application Password khusus situs, bukan password login biasa. Jangan bagikan .env.

```bash
python bot.py --check-site
python bot.py --check-auth
python bot.py --dry-run
```

Buka HTML yang dicetak dengan xdg-open, lalu:

```bash
python bot.py --from-preview data/financepress-HASH.json
```

Ganti HASH dengan nama sebenarnya. --from-preview langsung Publish meskipun .env
lama POST_STATUS=draft. Perintah tanpa --from-preview mengikuti POST_STATUS.
Preview lengkap menampilkan judul, kategori, tag, excerpt, slug, jumlah kata dan gambar.
Mengedit HTML tidak mengubah JSON; JSON adalah data yang diunggah.

## Pilihan penting

- --dry-run: membuat preview lokal; API teks/gambar tetap berbayar.
- --category bisnis: fokus satu dari enam kategori. Tanpa opsi, kategori lebih jarang
  diprioritaskan jika memiliki sumber relevan yang cukup.
- --revise-url URL: siapkan revisi mendalam dari artikel situs sendiri, belum upload.
- --rewrite-preview FILE.json: siapkan ulang preview lama, belum upload.
- --from-preview FILE.json: upload versi yang diperiksa dan langsung Publish.
- --loop: jalankan siklus berulang sesuai INTERVAL_HOURS; server harus hidup.
  Jangan gabungkan dengan perintah revisi atau --from-preview.

Slug web berasal dari judul. Nama JSON/HTML lokal tetap hash stabil. Revisi menyimpan
ID post dan alias slug lama agar perubahan slug tidak membuat post kedua.

## Kualitas dan sumber

Target 900–1300 kata, minimum 700, 5–7 subbagian dengan beberapa paragraf, pembuka,
poin penting, implikasi/risiko dan rangkuman. Draf pendek/struktur salah diperbaiki
maksimal sekali. Artikel yang belum cukup bahan tidak dipaksakan terbit.
ARTICLE_MIN_WORDS dan ARTICLE_TARGET_WORDS dapat diatur di .env; default 700/1100.

RSS: CNBC Market/News/Entrepreneur, Detik Finance, ANTARA, Cointelegraph. Isi sumber
publik diekstrak dari paragraf artikel, tanpa melewati login/paywall. Feed tidak
menjamin sumber tiap kategori selalu ada. Tidak mengukur Google Trends.

URL sumber pada 100 post publik terbaru dan seluruh preview lokal diblokir untuk
post baru. Judul mirip dan tumpang-tindih isi ikut diperiksa. Ini mengurangi duplikat,
bukan jaminan sempurna untuk laporan kejadian sama dari sumber berbeda.

## Gambar AI

```dotenv
ENABLE_AI_IMAGE=true
IMAGE_MODEL=gpt-image-2.5-flare
IMAGE_QUALITY=low
IMAGE_SIZE=1536x1024
INLINE_IMAGE=true
```

Satu JPEG dibuat per artikel dan dipakai ulang bila tersedia. Gambar unggulan
serta gambar di awal isi diupload otomatis. INLINE_IMAGE=false mencegah gambar inline
baru jika tema sudah menampilkan featured image. Tampilan beranda tetap mengikuti tema.
Akses model/verifikasi organisasi bergantung akun API. Gambar dan artikel memakai
saldo. Timeout setelah API memproses tetap bisa berbiaya tanpa file berhasil tersimpan.

## Operasional

Akun perlu izin publish_posts, upload_files dan pembuatan tag baru bila diperlukan.
Tag dicari berdasarkan slug sebelum dibuat. Media/post dicari sebelum upload untuk
pemulihan timeout. Beberapa tag/media bisa tersimpan walau post berikutnya gagal;
ini bukan transaksi atomik lintas API. File checkpoint membantu melanjutkan.

Jalankan dari satu server dan simpan data/history.db beserta preview. Excerpt bukan
field khusus plugin SEO. Validasi sumber/struktur belum membuktikan semua klaim benar;
periksa angka, tanggal dan sumber resmi keuangan sebelum menerbitkan.

## Pengujian

```bash
python -m unittest discover -s tests -v
```

46 tes lokal memakai mock: penulisan panjang, sumber terkait, filter URL bekas,
prioritas kategori, slug, revisi pada ID lama, metadata, gambar dan publikasi.
Tidak ada API berbayar atau update live selama tes. Pembaca sumber publik dicoba
pada satu halaman sumber BEI; penulisan/update nyata perlu akun di komputermu.
