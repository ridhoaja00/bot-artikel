> Pembaruan terbaru: baca REVISI-KONTEN.md. Slug web kini dari judul; hash hanya nama file lokal. Untuk update terbaru ganti bot.py DAN config.json.

# Update gambar AI untuk bot yang sudah berjalan

## 1. Ganti hanya bot.py

Ekstrak ZIP ini ke folder lain. Buat cadangan dari terminal folder proyek lama:

```bash
cp -n bot.py bot-sebelum-gambar.py
```

Salin hanya `bot.py` dari ZIP ke:

```text
/home/mazor/Documents/python_otomatis/financepress/bot.py
```

Pertahankan `.env`, `config.json`, `.venv`, dan `data` yang sudah berhasil.
Tidak perlu dependensi baru. Perbaikan override isi `.env` dan perapihan spasi
kredensial WordPress sudah termasuk, sehingga perbaikan login sebelumnya tetap ada.

## 2. Pengaturan gambar

Gambar langsung aktif: satu JPEG landscape dengan gpt-image-2.5-flare, kualitas low,
ukuran 1536x1024. Memakai OPENAI_API_KEY yang sudah ada dan saldo tambahan per gambar.
Model gambar harus tersedia di akun API; verifikasi organisasi bisa diperlukan.
Tidak perlu mengubah OPENAI_MODEL yang dipakai untuk teks.

Opsional, tambahkan ini pada `.env` untuk mengatur fitur:

```dotenv
ENABLE_AI_IMAGE=true
IMAGE_MODEL=gpt-image-2.5-flare
IMAGE_QUALITY=low
IMAGE_SIZE=1536x1024
INLINE_IMAGE=true
```

Set ENABLE_AI_IMAGE=false untuk menonaktifkan gambar. Set INLINE_IMAGE=false
sebelum upload jika tema sudah menampilkan gambar unggulan di awal artikel.
Pengaturan ini tidak menghapus gambar inline pada artikel yang sudah terunggah.

## 3. Cek izin

```bash
python bot.py --check-auth
```

Versi ini juga memeriksa upload_files. Jika izin ini tidak tersedia, akun perlu
peran yang berhak mengunggah media, diatur oleh administrator situs.

## 4. Tambahkan gambar pada preview yang sudah berhasil

Dari folder proyek lama dengan .venv aktif:

```bash
python bot.py --dry-run --from-preview data/financepress-2642867ae9784eae7919f62e.json
xdg-open data/financepress-2642867ae9784eae7919f62e.html
```

JSON dibuat bersama HTML pada versi sebelumnya. Teks yang sama dipakai, tanpa AI
penulis lagi; gambar baru menggunakan API berbayar. Tidak ada upload dalam dry-run.
Jika JSON itu sudah dihapus, buat preview baru dengan python bot.py --dry-run.

## 5. Upload teks dan gambar yang sama

**Perilaku terbaru:** --from-preview langsung Publish, termasuk bila .env lama
masih berisi POST_STATUS=draft. Periksa preview lebih dahulu, lalu:

```bash
python bot.py --from-preview data/financepress-2642867ae9784eae7919f62e.json
```

JPEG yang sudah tersimpan dipakai ulang; jangan menghapusnya agar tidak meminta
pembuatan gambar lagi. Gambar masuk Media Library, menjadi Gambar Unggulan dan,
jika INLINE_IMAGE=true, muncul di awal isi artikel dengan label ilustrasi AI.
Jika artikel dengan slug itu sudah ada, bot memperbarui artikel yang sama
dengan isi/metadata preview dan menerbitkannya. Gambar unggulan yang sudah ada
dipakai kembali. Edit redaksi di WordPress bisa tertimpa oleh preview JSON.
Panduan alur lengkap ada di SIAP-PUBLISH.md.

Untuk artikel baru berikutnya:

```bash
python bot.py --dry-run
python bot.py --loop
```

--loop dapat membuat teks dan gambar berulang kali dan mengurangi saldo API.
Gunakan setelah hasil satu artikel sesuai. Perhatikan potensi dua gambar yang sama
jika tema menampilkan featured image sekaligus gambar inline.

## Jika gagal

- Gambar AI HTTP 403/model_not_found: cek nama/akses model dan verifikasi organisasi
  bila diminta dashboard. Akses model teks belum membuktikan akses gambar tersedia.
- insufficient_quota/credit_balance_exhausted: cek saldo dan organisasi API key.
- WordPress HTTP 401: cek username/password aplikasi yang sebelumnya berhasil.
- WordPress HTTP 403 saat media: cek izin upload dan pembatasan hosting.
- HTTP 413: ukuran file melewati batas hosting. Untuk gambar baru bisa pilih
  IMAGE_SIZE=1024x1024. Gambar cache tidak otomatis berubah saat pengaturan diubah.
- Timeout: lanjutkan dengan --from-preview. Teks sudah tersimpan. Jika API gambar
  sempat memproses tetapi JPEG belum tersimpan, pengulangan tetap dapat berbiaya.

46 tes lokal lulus memakai mock. Generasi gambar dan upload nyata belum diuji
dengan API key/kredensial kamu dari lingkungan ini.
