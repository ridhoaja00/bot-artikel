> Pembaruan terbaru: baca REVISI-KONTEN.md. Slug web kini dari judul; hash hanya nama file lokal. Untuk update terbaru ganti bot.py DAN config.json.

# Preview → langsung Publish

Versi ini menyiapkan judul, isi artikel, excerpt/ringkasan, kategori situs, 3–5 tag,
gambar AI, alt text, dan label ilustrasi. Setelah preview diperiksa, satu perintah
mengunggah sekaligus menerbitkan artikel. Tidak perlu mengisi kolom manual di WP.

## Update satu kali

Ekstrak ZIP ke folder lain dan ganti hanya bot.py pada proyek lama:

```text
/home/mazor/Documents/python_otomatis/financepress/bot.py
```

Pertahankan .env, config.json, .venv, dan data yang sudah berhasil. Tidak ada
dependensi baru. Perbaikan login dari percakapan sebelumnya sudah termasuk.

## Preview yang sudah kamu punya

Lengkapi preview lama sekali dengan tag/metadata dan gambar bila belum tersedia:

```bash
python bot.py --dry-run --from-preview data/financepress-2642867ae9784eae7919f62e.json
```

Ini tidak menulis ulang judul atau isi artikel. AI dipakai untuk metadata yang
belum ada dan gambar yang belum tersimpan, sehingga tetap dapat memakai saldo.
Preview HTML ditulis kembali dengan panel kategori, tag, excerpt, gambar dan status.

Buka dan periksa:

```bash
xdg-open data/financepress-2642867ae9784eae7919f62e.html
```

Kalau sesuai, publikasikan langsung:

```bash
python bot.py --from-preview data/financepress-2642867ae9784eae7919f62e.json
```

**Perintah ini langsung Publish**, meskipun .env lama masih POST_STATUS=draft.
Bot memakai judul dan isi yang sama. Tag yang sudah ada dipakai ulang; tag baru
dibuat otomatis. Gambar diupload sebagai Featured Image dan, jika INLINE_IMAGE=true,
di awal isi. Jika teks/metadata dan JPEG sudah tersimpan, upload tidak memanggil AI
penulis/gambar lagi. URL hasil ditampilkan di terminal.

Tidak ada langkah konfirmasi tambahan di terminal. Menjalankan --from-preview tanpa
--dry-run adalah perintah kamu untuk menerbitkan versi JSON yang dipilih.

## Artikel berikutnya

```bash
python bot.py --dry-run
```

Perhatikan nama HTML/JSON yang dicetak bot, lalu buka HTML tersebut dengan xdg-open.
Setelah diperiksa, pakai --from-preview dengan JSON yang memiliki nama sama.
Nama hash berbeda untuk setiap kumpulan sumber; bukan selalu nama contoh di atas.

## Artikel lama dan pengulangan perintah

Jika slug sudah ada sebagai draft, artikel itu diperbarui menjadi Publish, bukan
membuat artikel kedua. Judul/isi/metadata dari JSON adalah versi yang dipakai;
edit yang dilakukan terpisah di WordPress bisa tertimpa. Jika publikasi telah
berhasil dan checkpoint lokal tersimpan, mengulang perintah untuk preview yang
sama akan melewati artikel yang sudah terbit. Ini tidak menjamin transaksi lintas
API: pada timeout, media/tag mungkin sudah dibuat dan akan dicari lagi saat retry.

HTML untuk melihat, JSON untuk mengunggah. Mengedit HTML tidak mengubah isi JSON.
Hash file lokal tetap dipertahankan; slug web artikel baru/revisi berasal dari judul.

## Izin dan batas

Akun WordPress perlu izin publish_posts dan upload_files bila gambar aktif.
Untuk tag baru diperlukan izin membuat tag; biasanya gunakan akun editor/admin
yang sesuai kebijakan situs. Jika akses ditolak, bot menampilkan error tanpa
mencetak password atau API key. Jangan membagikan .env.

Gambar tetap menggunakan API berbayar; akses model gambar harus tersedia di akun.
Metadata baru dari preview lama juga memakai API satu kali. Excerpt bukan field
plugin SEO khusus. Foto/gambar pada kartu beranda tergantung template tema.
Periksa sumber, angka dan tanggal informasi finansial pada preview sebelum terbit.

46 pengujian lokal lulus dengan mock. Tidak ada publikasi atau pemakaian API
berbayar dari lingkungan pembuat proyek; uji nyata memakai kredensial di komputermu.
