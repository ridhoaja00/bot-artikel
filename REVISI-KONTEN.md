# Artikel mendalam, slug judul, dan kategori yang lebih beragam

## Yang diperbaiki

Versi sebelumnya hanya memakai ringkasan RSS, sehingga pembahasan bisa berhenti
pada beberapa paragraf. Versi ini membaca paragraf publik pada halaman sumber
terpilih, menyaring keterkaitan topiknya, lalu menargetkan 900–1300 kata.
Minimum bawaan 700 kata dan 5–7 subbagian, masing-masing minimal dua paragraf.
Draf pendek/struktur salah dicoba diperbaiki sekali. Jika bahan tidak cukup,
proses berhenti, bukan mengarang fakta atau mengisi paragraf berulang.

Judul informatif dan menarik; pembuka, poin penting, pembahasan mekanisme/konteks,
implikasi, risiko dan rangkuman. Nomor sumber dibuat lebih kecil dan tanggal sumber
lebih ringkas. Baca juga memakai tautan artikel situs yang memang tersedia.

Slug web dibuat dari judul, misalnya demutualisasi-bei-berubah-investor. File lokal
masih financepress-HASH.json/.html agar alur terminal dan pelacakan tetap stabil.
Hash bukan lagi slug web untuk artikel baru/revisi yang disiapkan versi ini.

## Update sekali

Ekstrak ZIP ke folder lain, buat cadangan bot.py dan config.json lama, lalu ganti
**bot.py dan config.json** di proyek yang sudah berjalan. Jangan menimpa .env,
data, atau .venv. Tidak ada dependensi baru. config.json baru menambah RSS News,
Entrepreneur dan Detik Finance agar pasokan topik lebih luas; kredensial tetap .env.

## Perbaiki artikel BEI yang sudah terbit

Cara ini membaca URL publik dan menyimpan ID post yang benar, bukan membuat post
kedua saat slug berubah. Menyiapkan preview belum mengubah WordPress.

```bash
python bot.py --revise-url "https://allaboutmoney.id/2026/10/28/financepress-6bfeb712ed3442f568cb24bb/"
```

Jika berhasil:

```bash
xdg-open data/financepress-6bfeb712ed3442f568cb24bb.html
```

Periksa isi, sumber, kategori, jumlah kata dan slug. Untuk menerapkan revisi pada
post yang sama dan menerbitkannya:

```bash
python bot.py --from-preview data/financepress-6bfeb712ed3442f568cb24bb.json
```

URL baru dicetak sesudah update. Teks dan slug lama berubah hanya setelah langkah
upload tersebut. Periksa tautan lama setelah perubahan; pengalihan URL mengikuti
perilaku dan konfigurasi WordPress/hosting, tidak dijamin oleh skrip ini.
Gambar unggulan lama digunakan kembali jika ID/URL masih tersedia, sehingga
revisi tidak perlu meminta gambar berbayar baru hanya karena slug berubah.
Penyusunan ulang artikel tetap memakai saldo API teks.

Jika JSON lama masih tersedia, alternatif persiapannya:

```bash
python bot.py --rewrite-preview data/financepress-6bfeb712ed3442f568cb24bb.json
```

Gunakan --revise-url ATAU --rewrite-preview, bukan keduanya sekaligus. Cadangan JSON
sebelum revisi disimpan sebagai .before-revision.json. Revisi menimpa versi preview
setelah penulisan baru berhasil; artikel live belum berubah sampai --from-preview.

## Post baru

```bash
python bot.py --dry-run
```

Bot mengecualikan URL sumber dari 100 post publik terbaru dan seluruh preview lokal,
termasuk preview yang belum dipublikasikan. Parameter pelacakan pada URL tidak bisa
membuat sumber lama dianggap baru. Judul mirip dan tumpang-tindih isi juga diperiksa.
Kategori yang lebih jarang muncul diprioritaskan, sesuai ketersediaan bahan relevan.
Tidak menjamin semua kategori mendapat artikel setiap putaran jika sumber kurang.

Nama file baru dicetak di terminal. Buka HTML itu, kemudian --from-preview JSON
bernama sama untuk langsung Publish. Tidak otomatis memuat ulang preview lama
hanya untuk membuat gambar lain. Untuk membuka preview tertentu gunakan namanya.

## Pilih kategori tertentu

```bash
python bot.py --dry-run --category keuangan-pribadi
python bot.py --dry-run --category investasi
python bot.py --dry-run --category trading
python bot.py --dry-run --category crypto
python bot.py --dry-run --category ekonomi
python bot.py --dry-run --category bisnis
```

Jalankan salah satu sesuai kebutuhan, bukan semua jika tidak diperlukan. Bila
kategori itu tidak memiliki sumber baru yang cukup, bot tidak mengarang artikel.
RSS Market, News, Entrepreneur, Detik Finance, ANTARA dan Cointelegraph dapat berubah
atau tidak dapat diakses dari jaringan tertentu; konfigurasi sumber bisa disesuaikan.

## Biaya dan batas

Membaca sumber publik tidak memakai OpenAI, tetapi menulis artikel panjang dan satu
percobaan perbaikan otomatis memakai lebih banyak token daripada versi pendek.
Gambar baru juga memakai biaya API; gambar lama yang tersedia digunakan kembali
pada revisi. Tidak melewati login/paywall. Sumber yang tidak dapat dibaca memakai
ringkasan terbuka; bila bahan total kurang, penulisan ditolak sebelum API penulis.

Pencegahan duplikasi bukan jaminan semantik mutlak: sumber baru dapat melaporkan
kejadian yang sama dengan istilah berbeda. Pemilihan AI dan pemeriksaan judul/isi
membantu, sementara pemblokiran URL mencegah penggunaan ulang sumber yang tercatat.
Pertahankan folder data dan jalankan hanya dari satu server agar riwayat tidak hilang.

46 tes lokal lulus dengan mock. Pembaca halaman publik telah dicoba pada satu sumber
artikel BEI dan berhasil mengekstrak paragrafnya. Model penulis/gambar dan update
live tidak dijalankan dari sini karena kredensial berada di komputermu. Seluruh
angka, tanggal dan kesimpulan finansial tetap perlu diperiksa di preview.
