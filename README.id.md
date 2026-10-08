# Hololive Dreams Auto Fishing

[Masalah yang diketahui dan solusi sementara](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/main/docs/KNOWN_ISSUES.md)

[繁體中文](README.md) · [简体中文](README.zh-CN.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Asisten memancing otomatis untuk **hololive Dreams** versi Windows. Aplikasi memakai pengenalan layar dan input mouse biasa untuk menangani sambaran, menarik ikan, hasil tangkapan, dan ronde berikutnya.

## Unduh

Buka [GitHub Releases](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/releases/latest) dan unduh `Hololive-Dreams-Fishing-Auto-v1.1.1.exe` dari lampiran rilis.

Cukup jalankan satu file EXE ini.

## Fitur

- Mengenali tanda sambaran, melacak ikan dan zona tangkapan, serta mengendalikan penarikan ikan.
- Menangani tombol Lanjut / Berikutnya pada layar hasil serta menutup pop-up entri ensiklopedia baru dan item untuk melanjutkan memancing.
- Enam bahasa: 繁體中文, 简体中文, English, 日本語, 한국어, dan Indonesian. Memilih bahasa akan mengubah antarmuka dan pesan asisten.
- Menampilkan jumlah tangkapan pada sesi saat ini. Atur target tangkapan agar asisten berhenti setelah target tercapai.
- Pintasan mulai bawaan adalah F8 dan berhenti F9. Klik masing-masing kolom pengaturan lalu tekan tombol atau kombinasi baru untuk mengubahnya. Kedua pintasan tidak boleh bertabrakan.
- Riwayat aktivitas.
- Diagnostik pengembang lokal opsional.

## Cara menggunakan

1. Buka game, siapkan umpan, dan masuk ke layar memancing.
2. Jalankan EXE dan pilih bahasa pada “Bahasa / Language”.
3. Atur target tangkapan; `0` berarti tanpa batas. Untuk mengubah pintasan berhenti, klik kolomnya lalu tekan kombinasi yang diinginkan.
4. Klik Mulai atau tekan pintasan mulai. Asisten mencoba mengaktifkan game; pertahankan game di depan dengan seluruh tampilannya terlihat selama berjalan.
5. Berhenti dengan pintasan berhenti, tombol Berhenti, atau berpindah jendela. Memulai lagi akan mengatur hitungan ke nol dan menghitung target tangkapan dari awal.

## Persyaratan dan batasan

Memerlukan Windows 10 / 11 x64 dan game versi Windows. Pertahankan area klien game pada 16:9; jangan minimalkan, tutupi, atau ubah ukuran jendela saat berjalan. Memancing di latar belakang dan melanjutkan memancing setelah pergantian hari pada pukul 05.00 JST tidak didukung. Asisten tidak otomatis membeli umpan, berpindah peta, atau mengisi ulang sumber daya game.

Warna karakter, animasi, resolusi, kinerja, dan pembaruan game masih dapat memengaruhi pengenalan dan input; hentikan dan berikan data diagnostik jika terjadi masalah. Ini adalah alat tidak resmi yang tidak membaca atau mengubah memori proses, data simpanan, atau file game. Alat ini hanya ditujukan untuk pembelajaran pemrograman Python serta penelitian dan pertukaran pengetahuan tentang teknologi pengenalan gambar. Periksa sendiri aturan game mengenai penggunaan alat otomatisasi. Jangan gunakan alat ini untuk merusak ekosistem game atau untuk tujuan komersial maupun mencari keuntungan. Pengembang tidak bertanggung jawab atas masalah apa pun yang timbul akibat penggunaan alat ini.

## Melaporkan masalah dan Mode pengembang

Laporkan kegagalan melanjutkan ronde, masalah pelacakan, atau masalah lain melalui [GitHub Issues](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/issues).

Aktifkan Mode pengembang sebelum mengulangi masalah. Mode ini menyimpan tangkapan layar status, kartu tangkapan, data pelacakan, dan waktu pemrosesan secara lokal; tidak ada unggahan otomatis. Tangkapan layar berisi tampilan game, dan diagnostik menambah beban kinerja.

Klik `?` di sebelah Mode pengembang untuk melihat dan membuka folder diagnostik:

JPEG disimpan di latar belakang, maksimum 192 KiB per gambar. Sebanyak 64 gambar kejadian terakhir dan tampilan terbaru disimpan, beserta dua segmen pelacakan terakhir masing-masing 4 MiB. ZIP diagnostik tidak menyertakan video opsional.

```text
%LOCALAPPDATA%\HololiveFishingAuto\sessions\
```

Lokasi mengikuti akun Windows Anda. Setiap sesi membuat folder bernama waktu. Sertakan versi aplikasi, bahasa / karakter game, resolusi, skala tampilan Windows, deskripsi masalah, dan `diagnostics-YYYY-MM-DD_HH-MM-SS.zip` yang dibuat otomatis setelah berhenti. Periksa tangkapan layar sebelum membagikannya agar tidak ada informasi yang tidak ingin dipublikasikan.

## Kode sumber dan lisensi

Lihat [panduan pengembangan](docs/DEVELOPMENT.md) untuk menjalankan kode sumber, membuat EXE tunggal, dan pengujian offline. Kode berlisensi [MIT](LICENSE); hak atas karakter ikan dan game tetap milik pemilik masing-masing.
