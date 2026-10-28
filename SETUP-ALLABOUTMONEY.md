> Pembaruan terbaru: baca REVISI-KONTEN.md. Slug web kini dari judul; hash hanya nama file lokal. Untuk update terbaru ganti bot.py DAN config.json.

> Versi terbaru: --from-preview langsung Publish. Baca SIAP-PUBLISH.md.
> Perintah tanpa --from-preview tetap mengikuti POST_STATUS.

# Bot artikel untuk AllAboutMoney.id

Versi ini disesuaikan dengan situs **https://allaboutmoney.id**. Pemeriksaan publik
pada 28 Oktober 2026 berhasil membaca beranda, artikel, kategori, dan dukungan
Application Passwords. Belum ada artikel yang diunggah atau perubahan pada situs.

## 1. Pasang di Linux

Ekstrak ZIP, buka terminal dalam folder `financepress`, lalu:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Jika `venv` tidak tersedia di Ubuntu/Debian, pasang paket `python3-venv` melalui
package manager sistem, lalu ulangi. Pada Windows jalankan melalui WSL.

## 2. Isi koneksi

Buka `.env` dengan editor. Alamat situs sudah terisi:

```dotenv
WP_URL=https://allaboutmoney.id
WP_USERNAME=isi_username_wordpress_kamu
WP_APP_PASSWORD=isi_application_password_kamu
OPENAI_API_KEY=isi_api_key_kamu
OPENAI_MODEL=isi_model_yang_tersedia_di_akun_api
POST_STATUS=draft
INTERVAL_HOURS=12
```

Buat Application Password dari **https://allaboutmoney.id/wp-admin/profile.php**:
bagian **Application Passwords / Kata Sandi Aplikasi**, beri nama `FinancePress`,
lalu salin password yang dihasilkan ke `.env`. Gunakan username akun WordPress,
bukan nama tampilan. Password aplikasi dapat memuat spasi; salin sebagai satu nilai.
Jangan kirim kredensial melalui chat. API AI memerlukan akses dan saldo sendiri.

## 3. Periksa dan coba

```bash
# Tanpa biaya AI dan tanpa menulis ke situs
python bot.py --check-site
python bot.py --check-auth

# Menggunakan API AI; hanya menyimpan preview di folder data
python bot.py --dry-run

# Menggunakan API AI, kemudian mengunggah satu draft
python bot.py
```

Buka **https://allaboutmoney.id/wp-admin/edit.php?post_status=draft&post_type=post**
untuk memeriksa hasil. Jika sudah cocok, ubah `POST_STATUS=publish` untuk publikasi
otomatis. `draft` tetap menjadi pengaturan awal karena referensi yang terpasang
belum membuktikan semua klaim finansial benar.

Untuk menjalankan terus sesuai interval:

```bash
python bot.py --loop
```

Komputer atau VPS harus tetap menyala. Interval adalah jeda setelah satu siklus
selesai, bukan jadwal jam tertentu. Contoh cron tersedia di README.

## Penyesuaian yang sudah dibuat

| Kategori situs | Slug | ID hasil pemeriksaan |
| --- | --- | --- |
| Keuangan Pribadi | keuangan-pribadi | 814815 |
| Investasi | investasi | 814816 |
| Trading | trading | 814817 |
| Crypto | crypto | 814818 |
| Ekonomi | ekonomi | 814819 |
| Bisnis | bisnis | 814820 |

Bot membaca ulang kategori dari situs sebelum menulis, lalu memetakan kategori
pilihan AI ke ID aktual. Jika kategori yang diperlukan hilang, proses berhenti
agar artikel tidak salah masuk kategori. Bot tidak membuat kategori baru.

Gaya penulisan mengikuti arah situs: bahasa sederhana, sapaan Anda, inti informasi
lebih dahulu, pembahasan dampak dan risiko, tanpa emoji atau judul sensasional.
Artikel memakai heading dan paragraf HTML yang mengikuti tema WordPress.
Judul dan excerpt disiapkan untuk tampilan daftar artikel.

Judul 50 artikel terakhir di situs serta riwayat lokal dipakai untuk mengurangi
pengulangan. Pos bawaan `Halo Dunia!` diabaikan oleh pemilihan topik.
Pencegahan duplikasi semantik masih bergantung pada pemilihan AI; bukan jaminan.

Sumber awal: RSS CNBC Indonesia Market, ANTARA Ekonomi, dan Cointelegraph. Ketiganya
berhasil mengembalikan feed saat diperiksa, tetapi dapat berubah atau tidak
dapat diakses dari jaringan lain. Feed CoinDesk tidak dipakai karena ringkasannya
kosong saat diuji. Berita ANTARA yang melewati batas usia juga dilewati. Pengamatan tren memakai kebaruan dan liputan
lintas domain, bukan Google Trends. Dukungan topik keuangan pribadi dan bisnis
bergantung pada ketersediaan sumber; tambahkan feed di `config.json` bila perlu.

## Jika belum berhasil

- **`--check-site` gagal:** pastikan situs dan `/wp-json/` bisa dibuka, tidak ada
  pemblokiran koneksi/REST API, serta slug kategori sesuai `config.json`.
- **`--check-auth` gagal:** cek username dan Application Password, izin akun, serta
  apakah hosting meneruskan header Authorization. Dukungan yang diiklankan API
  belum menjamin kredensial akun diterima; tes ini tidak membuat postingan.
- **API AI gagal:** cek API key, akses model dengan Chat Completions + JSON output,
  saldo, dan koneksi. Model sengaja tidak dikunci ke satu model tertentu.
- **Tidak ada artikel:** tidak ada satu topik dengan minimal dua domain sumber
  baru yang cukup relevan. Ini bisa terjadi meskipun masing-masing feed aktif.

Versi gambar AI tersedia; baca UPDATE-GAMBAR-AI.md. Bot tidak mengubah tema, menu, halaman
kategori, atau artikel lama. Pengecekan klaim terhadap sumber resmi BI/OJK/BPS
belum otomatis; periksa khususnya angka, tanggal, dan aturan sebelum terbit.
